import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from gmail_helper.api.email_service.rules_processor import RulesProcessor
from gmail_helper.common.contracts.rules_contract import ActionType


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
        # Store mock returns a list of emails
        self.mock_store = Mock()
        self.mock_store.get_last_n_emails.return_value = [make_email()]

        # GmailClient mock
        self.mock_gmail = Mock()

        # RulesProcessor under test
        self.rp = RulesProcessor(self.mock_store, rules_file="rules.json", gmail_client=self.mock_gmail)

    def test_mark_as_read(self):
        rule = Mock()
        rule.description = "read"
        rule.actions = [Mock(type=ActionType.mark_as_read)]
        rule.conditions = []
        rule.match = "all"

        with (
            patch.object(self.rp, "load_rules", return_value=[rule]),
            patch.object(self.rp, "_matches", return_value=True),
        ):
            count = self.rp.apply_rules(limit=1)

        self.assertEqual(count, 1)
        self.mock_gmail.modify_message.assert_called_once_with("e1", add_label_ids=[], remove_label_ids=["UNREAD"])

    def test_mark_as_unread(self):
        rule = Mock()
        rule.description = "unread"
        rule.actions = [Mock(type=ActionType.mark_as_unread)]
        rule.conditions = []
        rule.match = "all"

        with (
            patch.object(self.rp, "load_rules", return_value=[rule]),
            patch.object(self.rp, "_matches", return_value=True),
        ):
            count = self.rp.apply_rules(limit=1)

        self.assertEqual(count, 1)
        self.mock_gmail.modify_message.assert_called_once_with("e1", add_label_ids=["UNREAD"], remove_label_ids=[])

    def test_move_message_inbox(self):
        action = Mock(type=ActionType.move_message, mailbox="Inbox")
        rule = Mock(description="move", actions=[action], conditions=[], match="all")

        with (
            patch.object(self.rp, "load_rules", return_value=[rule]),
            patch.object(self.rp, "_matches", return_value=True),
        ):
            count = self.rp.apply_rules(limit=1)

        self.assertEqual(count, 1)
        args, kwargs = self.mock_gmail.modify_message.call_args
        self.assertEqual(kwargs["add_label_ids"], ["INBOX"])
        self.assertEqual(kwargs["remove_label_ids"], [])

    def test_move_message_new_label(self):
        self.mock_gmail.create_label.return_value = {"id": "LBL_NEW"}
        action = Mock(type=ActionType.move_message, mailbox="Work")
        rule = Mock(description="move", actions=[action], conditions=[], match="all")

        with (
            patch.object(self.rp, "load_rules", return_value=[rule]),
            patch.object(self.rp, "_matches", return_value=True),
        ):
            self.rp.apply_rules(limit=1)

        self.mock_gmail.create_label.assert_called_once_with("Work")
        self.mock_gmail.modify_message.assert_called_once()
        add_ids = self.mock_gmail.modify_message.call_args.kwargs["add_label_ids"]
        self.assertIn("LBL_NEW", add_ids)

    def test_warm_labels_cache_populates(self):
        self.mock_gmail.list_labels.return_value = [
            {"id": "LBL1", "name": "Work"},
            {"id": "LBL2", "name": "Personal"},
        ]
        self.rp._warm_labels_cache()
        self.assertEqual(self.rp._label_cache["work"], "LBL1")
        self.assertEqual(self.rp._label_cache["personal"], "LBL2")
