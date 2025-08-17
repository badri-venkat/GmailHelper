import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from gmail_helper.common.contracts.rules_contract import ActionType, Rule
from gmail_helper.worker.rules_processor import RulesProcessor


class MockAction:
    def __init__(self, type_, mailbox=None):
        self.type = type_
        self.mailbox = mailbox


class MockRule:
    def __init__(self, desc, actions, match="all", conditions=None):
        self.description = desc
        self.actions = actions
        self.match = match
        self.conditions = conditions or []


class MockStore:
    def __init__(self, emails):
        self._emails = emails

    def get_last_n_emails(self, n):
        return self._emails[:n]


def make_email(eid="e1", subject="hello"):
    return {
        "id": eid,
        "subject": subject,
        "sender": "a@example.com",
        "snippet": "body",
        "received_datetime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


class TestRulesProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_store = MockStore([make_email()])
        self.mock_gmail = MagicMock()

    def test_mark_as_read_no_gmail_logs_only(self):
        rp = RulesProcessor(self.mock_store, gmail_client=None)
        rule = MockRule("read", [MockAction(ActionType.mark_as_read)])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(rp, "_matches", return_value=True):
            count = rp.apply_rules(limit=5)

        self.assertEqual(count, 1)

    def test_mark_as_read_with_gmail_calls_modify(self):
        rp = RulesProcessor(self.mock_store, gmail_client=self.mock_gmail)
        rule = MockRule("read", [MockAction(ActionType.mark_as_read)])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(rp, "_matches", return_value=True):
            count = rp.apply_rules(limit=1)

        self.assertEqual(count, 1)
        self.mock_gmail.modify_message.assert_called_once_with("e1", add_label_ids=[], remove_label_ids=["UNREAD"])

    def test_mark_as_unread_with_gmail_calls_modify(self):
        rp = RulesProcessor(self.mock_store, gmail_client=self.mock_gmail)
        rule = MockRule("unread", [MockAction(ActionType.mark_as_unread)])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(rp, "_matches", return_value=True):
            count = rp.apply_rules(limit=1)

        self.assertEqual(count, 1)
        self.mock_gmail.modify_message.assert_called_once_with("e1", add_label_ids=["UNREAD"], remove_label_ids=[])

    def test_move_message_inbox(self):
        """Moving to Inbox should add INBOX, not remove it"""
        rp = RulesProcessor(self.mock_store, gmail_client=self.mock_gmail)
        rp._label_cache = {"inbox": "INBOX"}
        rule = MockRule("move", [MockAction(ActionType.move_message, "Inbox")])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(rp, "_matches", return_value=True):
            count = rp.apply_rules(limit=1)

        self.assertEqual(count, 1)
        self.mock_gmail.modify_message.assert_called_once()
        args, kwargs = self.mock_gmail.modify_message.call_args
        self.assertEqual(kwargs["add_label_ids"], ["INBOX"])
        self.assertEqual(kwargs["remove_label_ids"], [])

    def test_move_message_new_label_created(self):
        """If label not in cache, should call create_label and then modify_message"""
        self.mock_gmail.create_label.return_value = {"id": "LBL_NEW"}
        rp = RulesProcessor(self.mock_store, gmail_client=self.mock_gmail)
        rule = MockRule("move", [MockAction(ActionType.move_message, "Work")])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(rp, "_matches", return_value=True):
            rp.apply_rules(limit=1)

        self.mock_gmail.create_label.assert_called_once_with("Work")
        self.mock_gmail.modify_message.assert_called_once()
        args, kwargs = self.mock_gmail.modify_message.call_args
        self.assertIn("LBL_NEW", kwargs["add_label_ids"])
        self.assertIn("INBOX", kwargs["remove_label_ids"])

    def test_warm_labels_cache_populates_cache(self):
        self.mock_gmail.list_labels.return_value = [
            {"id": "LBL1", "name": "Work"},
            {"id": "LBL2", "name": "Personal"},
        ]
        rp = RulesProcessor(self.mock_store, gmail_client=self.mock_gmail)
        rp._warm_labels_cache()
        self.assertTrue("work" in rp._label_cache)
        self.assertEqual(rp._label_cache["work"], "LBL1")
