import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from gmail_helper.common.config import config
from gmail_helper.common.contracts.rules_contract import ActionType, DatePredicate, FieldName, Rule, StringPredicate
from gmail_helper.common.services.gmail_service import GmailClient
from gmail_helper.common.utils.logger import get_logger

LOG = get_logger(__name__)


class RulesProcessor:
    """
    Loads rules from JSON and applies them to emails from the store.
    Uses GmailClient for real actions (mark_as_read/unread, move via labels).
    """

    def __init__(self, store, rules_file: str = None, gmail_client: Optional[GmailClient] = None):
        self.store = store
        self.rules_file = rules_file or config.RULES_FILE
        self.gmail = gmail_client  # GmailClient or None
        self._label_cache: Dict[str, str] = {}
        self._labels_loaded = False

    # -------- Rules lifecycle --------

    def load_rules(self) -> List[Rule]:
        with open(self.rules_file, "r") as f:
            data = json.load(f)
        rules_raw = data.get("rules", data) if isinstance(data, dict) else data
        return [Rule(**r) for r in rules_raw]

    def apply_rules(self, limit: int = 20) -> int:
        rules = self.load_rules()
        emails = self.store.get_last_n_emails(limit)
        total_actions = 0

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

    # -------- Matching --------

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

    # -------- Actions --------

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

    def _act_mark_read(self, email: dict) -> int:
        if self.gmail is None:
            LOG.info("    [ACTION] mark_as_read (LOG ONLY) -> email %s", email["id"])
            return 1
        try:
            self.gmail.modify_message(email["id"], add_label_ids=[], remove_label_ids=["UNREAD"])
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
            self.gmail.modify_message(email["id"], add_label_ids=["UNREAD"], remove_label_ids=[])
            LOG.info("    [ACTION] mark_as_unread -> email %s (APPLIED)", email["id"])
            return 1
        except Exception as e:
            LOG.error("    [ACTION] mark_as_unread FAILED for %s: %s", email["id"], e)
            return 0

    def _act_move_message(self, email: dict, mailbox: str) -> int:
        """
        'Move' implemented as:
          - Add target label (create if missing) for user labels.
          - Remove INBOX (archive) unless moving to Inbox itself.
        """
        if self.gmail is None:
            LOG.info(
                "    [ACTION] move_message (LOG ONLY) -> email %s to '%s'",
                email["id"],
                mailbox,
            )
            return 1
        try:
            label_id, remove_inbox = self._resolve_move_target(mailbox)
            add = []
            rem = []
            if label_id and label_id != "INBOX":
                add.append(label_id)
            elif label_id == "INBOX":
                add.append("INBOX")
            if remove_inbox:
                rem.append("INBOX")

            if not add and not rem:
                LOG.info(
                    "    [ACTION] move_message -> email %s already in desired state",
                    email["id"],
                )
                return 1

            self.gmail.modify_message(email["id"], add_label_ids=add, remove_label_ids=rem)
            LOG.info(
                "    [ACTION] move_message -> email %s to '%s' (APPLIED) add=%s remove=%s",
                email["id"],
                mailbox,
                add,
                rem,
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

    # -------- Labels helpers --------

    def _warm_labels_cache(self) -> None:
        if self._labels_loaded or self.gmail is None:
            return
        try:
            labels = self.gmail.list_labels()
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
        - 'Inbox' => ('INBOX', False)
        - otherwise ensure/create user label, remove INBOX (archive)
        """
        if mailbox.lower() == "inbox":
            return "INBOX", False

        label_id = self._label_cache.get(mailbox.lower())
        if label_id:
            return label_id, True

        try:
            created = self.gmail.create_label(mailbox)
            label_id = created.get("id")
            if label_id:
                self._label_cache[mailbox.lower()] = label_id
                LOG.info("Created label '%s' (id=%s)", mailbox, label_id)
                return label_id, True
        except Exception as e:
            LOG.error("Failed to create label '%s': %s", mailbox, e)

        # Fallback: archive only
        return None, True
