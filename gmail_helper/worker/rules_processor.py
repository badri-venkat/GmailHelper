import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from gmail_helper.common.contracts.rules_contract import (
    Rule,
    FieldName,
    StringPredicate,
    DatePredicate,
    ActionType,
)
from gmail_helper.common.utils.logger import get_logger
from gmail_helper.common.config import config

LOG = get_logger(__name__)


class RulesProcessor:
    """
    Loads rules from a JSON file and applies them to emails from the store.
    For mark_as_read, calls Gmail modify API when gmail_service is provided.
    """

    def __init__(self, store, rules_file: str = None, gmail_service: Optional[object] = None):
        self.store = store
        self.rules_file = rules_file or config.RULES_FILE
        self.gmail = gmail_service  # googleapiclient.discovery.Resource or None

    def load_rules(self) -> List[Rule]:
        with open(self.rules_file, "r") as f:
            data = json.load(f)
        rules_raw = data.get("rules", data) if isinstance(data, dict) else data
        return [Rule(**r) for r in rules_raw]

    def apply_rules(self, limit: int = 200) -> int:
        rules = self.load_rules()
        emails = self.store.get_last_n_emails(limit)
        total_actions = 0

        for rule in rules:
            LOG.info("Evaluating rule: %s", rule.description)
            for email in emails:
                if self._matches(rule, email):
                    LOG.info("  ✓ Matched email %s (%s)", email['id'], email.get('subject', ''))
                    total_actions += self._execute_actions(email, rule)
        LOG.info("Completed rules run: %d actions executed/logged", total_actions)
        return total_actions

    def _matches(self, rule: Rule, email: dict) -> bool:
        results = [self._eval_condition(c, email) for c in rule.conditions]
        return all(results) if rule.match == "all" else any(results)

    def _eval_condition(self, cond, email) -> bool:
        if cond.field == FieldName.From_:
            field_val = email.get("sender", "")
        elif cond.field == FieldName.To:
            field_val = ""  # not captured in demo
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

    def _execute_actions(self, email: dict, rule: Rule) -> int:
        count = 0
        for action in rule.actions:
            if action.type == ActionType.mark_as_read:
                # If we have a Gmail service, perform the API call. Otherwise log.
                if self.gmail is not None:
                    try:
                        self.gmail.users().messages().modify(
                            userId="me",
                            id=email["id"],
                            body={"removeLabelIds": ["UNREAD"]},
                        ).execute()
                        LOG.info("    [ACTION] mark_as_read -> email %s (APPLIED)", email['id'])
                    except Exception as e:
                        LOG.error("    [ACTION] mark_as_read FAILED for %s: %s", email['id'], e)
                else:
                    LOG.info("    [ACTION] mark_as_read (LOG ONLY) -> email %s", email['id'])
                count += 1

            elif action.type == ActionType.mark_as_unread:
                if self.gmail is not None:
                    try:
                        self.gmail.users().messages().modify(
                            userId="me",
                            id=email["id"],
                            body={"addLabelIds": ["UNREAD"]},
                        ).execute()
                        LOG.info("    [ACTION] mark_as_unread -> email %s (APPLIED)", email['id'])
                    except Exception as e:
                        LOG.error("    [ACTION] mark_as_unread FAILED for %s: %s", email['id'], e)
                else:
                    LOG.info("    [ACTION] mark_as_unread (LOG ONLY) -> email %s", email['id'])
                count += 1

            elif action.type == ActionType.move_message:
                # Still keeping "move" as log-only for simplicity (requires label mgmt)
                mailbox = action.mailbox or "Inbox"
                LOG.info("    [ACTION] move_message (LOG ONLY) -> email %s to '%s'", email['id'], mailbox)
                count += 1

            else:
                LOG.warning("    [ACTION] unknown action %s for email %s", action.type, email['id'])
        return count
