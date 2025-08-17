import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from gmail_helper.common.config import config
from gmail_helper.common.contracts.rules_contract import (ActionType,
                                                          DatePredicate,
                                                          FieldName, Rule,
                                                          StringPredicate)
from gmail_helper.common.utils.logger import get_logger

LOG = get_logger(__name__)


class RulesProcessor:
    """
    Loads rules from a JSON file and applies them to emails from the store.
    - mark_as_read / mark_as_unread use Gmail modify API if gmail_service is provided; else logs.
    - move_message:
        * If gmail_service is provided, ensures the label exists, adds it, and removes INBOX (archive).
        * Else, logs only.
    """

    def __init__(
        self, store, rules_file: str = None, gmail_service: Optional[object] = None
    ):
        self.store = store
        self.rules_file = rules_file or config.RULES_FILE
        self.gmail = gmail_service  # googleapiclient.discovery.Resource or None
        self._label_cache: Dict[str, str] = {}  # name_lower -> labelId
        self._labels_loaded = False

    # -------------------- Public API --------------------

    def load_rules(self) -> List[Rule]:
        with open(self.rules_file, "r") as f:
            data = json.load(f)
        rules_raw = data.get("rules", data) if isinstance(data, dict) else data
        return [Rule(**r) for r in rules_raw]

    def apply_rules(self, limit: int = 200) -> int:
        rules = self.load_rules()
        emails = self.store.get_last_n_emails(limit)
        total_actions = 0

        # Preload labels once if we can act
        if self.gmail is not None:
            self._warm_labels_cache()

        for rule in rules:
            LOG.info("Evaluating rule: %s", rule.description)
            for email in emails:
                if self._matches(rule, email):
                    LOG.info(
                        "  ✓ Matched email %s (%s)",
                        email["id"],
                        email.get("subject", ""),
                    )
                    total_actions += self._execute_actions(email, rule)

        LOG.info("Completed rules run: %d actions executed/logged", total_actions)
        return total_actions

    # -------------------- Matching --------------------

    def _matches(self, rule: Rule, email: dict) -> bool:
        results = [self._eval_condition(c, email) for c in rule.conditions]
        return all(results) if rule.match == "all" else any(results)

    def _eval_condition(self, cond, email) -> bool:
        if cond.field == FieldName.From_:
            field_val = email.get("sender", "")
        elif cond.field == FieldName.To:
            field_val = ""  # not captured in this demo
        elif cond.field == FieldName.Subject:
            field_val = email.get("subject", "")
        elif cond.field == FieldName.Message:
            field_val = email.get("snippet", "")
        elif cond.field == FieldName.DateReceived:
            field_val = email.get("received_datetime", "")
        else:
            field_val = ""

        if isinstance(cond.predicate, StringPredicate):
            fv = (field_val or "").lower()
            ev = str(cond.value).lower()
            if cond.predicate == StringPredicate.contains:
                return ev in fv
            if cond.predicate == StringPredicate.does_not_contain:
                return ev not in fv
            if cond.predicate == StringPredicate.equals:
                return fv == ev
            if cond.predicate == StringPredicate.does_not_equal:
                return fv != ev
            return False

        if isinstance(cond.predicate, DatePredicate):
            try:
                received = datetime.fromisoformat(field_val.replace("Z", "+00:00"))
            except Exception:
                return False
            now = datetime.now(timezone.utc)
            delta = now - received
            v = int(cond.value)
            if cond.predicate == DatePredicate.less_than_days:
                return delta < timedelta(days=v)
            if cond.predicate == DatePredicate.greater_than_days:
                return delta > timedelta(days=v)
            if cond.predicate == DatePredicate.less_than_months:
                return delta < timedelta(days=30 * v)
            if cond.predicate == DatePredicate.greater_than_months:
                return delta > timedelta(days=30 * v)
            return False

        return False

    # -------------------- Actions --------------------

    def _execute_actions(self, email: dict, rule: Rule) -> int:
        count = 0
        for action in rule.actions:
            if action.type == ActionType.mark_as_read:
                count += self._act_mark_read(email)
            elif action.type == ActionType.mark_as_unread:
                count += self._act_mark_unread(email)
            elif action.type == ActionType.move_message:
                mailbox = (action.mailbox or "Inbox").strip()
                count += self._act_move_message(email, mailbox)
            else:
                LOG.warning(
                    "    [ACTION] unknown action %s for email %s",
                    action.type,
                    email["id"],
                )
        return count

    # ---- mark_as_read / mark_as_unread ----

    def _act_mark_read(self, email: dict) -> int:
        if self.gmail is None:
            LOG.info("    [ACTION] mark_as_read (LOG ONLY) -> email %s", email["id"])
            return 1
        try:
            self.gmail.users().messages().modify(
                userId="me",
                id=email["id"],
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            LOG.info("    [ACTION] mark_as_read -> email %s (APPLIED)", email["id"])
            return 1
        except Exception as e:
            LOG.error("    [ACTION] mark_as_read FAILED for %s: %s", email["id"], e)
            return 0

    def _act_mark_unread(self, email: dict) -> int:
        if self.gmail is None:
            LOG.info("    [ACTION] mark_as_unread (LOG ONLY) -> email %s", email["id"])
            return 1
        try:
            self.gmail.users().messages().modify(
                userId="me",
                id=email["id"],
                body={"addLabelIds": ["UNREAD"]},
            ).execute()
            LOG.info("    [ACTION] mark_as_unread -> email %s (APPLIED)", email["id"])
            return 1
        except Exception as e:
            LOG.error("    [ACTION] mark_as_unread FAILED for %s: %s", email["id"], e)
            return 0

    # ---- move_message ----

    def _act_move_message(self, email: dict, mailbox: str) -> int:
        """
        Gmail 'move' is modeled as:
          - Add the target label (create if needed for user labels).
          - Remove 'INBOX' so it gets archived out of the inbox.
        Special-case: if mailbox == 'Inbox', we simply add INBOX (ensure present) and do NOT remove it.
        """
        if self.gmail is None:
            LOG.info(
                "    [ACTION] move_message (LOG ONLY) -> email %s to '%s'",
                email["id"],
                mailbox,
            )
            return 1

        try:
            target_label_id, remove_inbox = self._resolve_move_target(mailbox)
            body = {"addLabelIds": [], "removeLabelIds": []}

            if target_label_id and target_label_id != "INBOX":
                body["addLabelIds"].append(target_label_id)
            elif target_label_id == "INBOX":
                # moving to Inbox: ensure INBOX present; do NOT remove it
                body["addLabelIds"].append("INBOX")

            if remove_inbox:
                body["removeLabelIds"].append("INBOX")

            # Avoid empty modify calls
            if not body["addLabelIds"] and not body["removeLabelIds"]:
                LOG.info(
                    "    [ACTION] move_message -> email %s already in desired state",
                    email["id"],
                )
                return 1

            self.gmail.users().messages().modify(
                userId="me",
                id=email["id"],
                body=body,
            ).execute()

            LOG.info(
                "    [ACTION] move_message -> email %s to '%s' (APPLIED) add=%s remove=%s",
                email["id"],
                mailbox,
                body["addLabelIds"],
                body["removeLabelIds"],
            )
            return 1
        except Exception as e:
            LOG.error(
                "    [ACTION] move_message FAILED for %s to '%s': %s",
                email["id"],
                mailbox,
                e,
            )
            return 0

    # -------------------- Labels Helpers --------------------

    def _warm_labels_cache(self) -> None:
        """Load all labels into a name->id cache once."""
        if self._labels_loaded or self.gmail is None:
            return
        try:
            res = self.gmail.users().labels().list(userId="me").execute()
            labels = res.get("labels", []) or []
            for l in labels:
                name = (l.get("name") or "").strip()
                if not name:
                    continue
                self._label_cache[name.lower()] = l.get("id")
            self._labels_loaded = True
            LOG.info("Preloaded %d labels into cache", len(self._label_cache))
        except Exception as e:
            LOG.warning("Failed to preload labels: %s", e)

    def _resolve_move_target(self, mailbox: str):
        """
        Returns (label_id, remove_inbox_flag).
        - If mailbox == 'Inbox' (case-insensitive), return ('INBOX', False)
        - For other names, ensure/create user label and plan to remove INBOX (archive).
        """
        if mailbox.lower() == "inbox":
            return "INBOX", False

        # Try existing
        label_id = self._label_cache.get(mailbox.lower())
        if label_id:
            return label_id, True

        # Create user label if not present
        try:
            created = (
                self.gmail.users()
                .labels()
                .create(
                    userId="me",
                    body={
                        "name": mailbox,
                        "labelListVisibility": "labelShow",
                        "messageListVisibility": "show",
                    },
                )
                .execute()
            )
            label_id = created.get("id")
            if label_id:
                self._label_cache[mailbox.lower()] = label_id
                LOG.info("Created label '%s' (id=%s)", mailbox, label_id)
                return label_id, True
        except Exception as e:
            LOG.error("Failed to create label '%s': %s", mailbox, e)

        # Fallback: no label id (will no-op add), still archive by removing INBOX to simulate move
        return None, True
