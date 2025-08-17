import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from gmail_helper.common.contracts.rules_contract import ActionType
from gmail_helper.worker.rules_processor import RulesProcessor


class FakeAction:
    def __init__(self, type_, mailbox=None):
        self.type = type_
        self.mailbox = mailbox


class FakeRule:
    def __init__(self, description, actions):
        self.description = description
        self.actions = actions
        self.conditions = []
        self.match = "all"


class FakeStore:
    def __init__(self, emails):
        self._emails = emails

    def get_last_n_emails(self, limit):
        return self._emails[:limit]


def make_email(id_="e1", subject="hello"):
    return {
        "id": id_,
        "subject": subject,
        "sender": "a@example.com",
        "snippet": "test",
        "received_datetime": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }


class TestRulesProcessor(unittest.TestCase):
    def test_mark_as_read_log_only(self):
        """If gmail is None, mark_as_read just logs but counts as action"""
        email = make_email()
        store = FakeStore([email])
        rp = RulesProcessor(store, rules_file="dummy.json", gmail_service=None)

        rule = FakeRule("read all", [FakeAction(ActionType.mark_as_read)])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(
            rp, "_matches", return_value=True
        ):
            count = rp.apply_rules(limit=5)

        self.assertEqual(count, 1)

    def test_mark_as_read_with_gmail(self):
        """mark_as_read should call gmail.users().messages().modify"""
        email = make_email()
        store = FakeStore([email])
        gmail = MagicMock()
        gmail.users.return_value.messages.return_value.modify.return_value.execute.return_value = (
            {}
        )

        rp = RulesProcessor(store, rules_file="dummy.json", gmail_service=gmail)
        rule = FakeRule("read all", [FakeAction(ActionType.mark_as_read)])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(
            rp, "_matches", return_value=True
        ):
            count = rp.apply_rules(limit=5)

        self.assertEqual(count, 1)
        gmail.users.return_value.messages.return_value.modify.assert_called_once()
        args, kwargs = gmail.users.return_value.messages.return_value.modify.call_args
        self.assertIn("removeLabelIds", kwargs["body"])

    def test_mark_as_unread_with_gmail(self):
        """mark_as_unread should call gmail.users().messages().modify"""
        email = make_email()
        store = FakeStore([email])
        gmail = MagicMock()
        gmail.users.return_value.messages.return_value.modify.return_value.execute.return_value = (
            {}
        )

        rp = RulesProcessor(store, rules_file="dummy.json", gmail_service=gmail)
        rule = FakeRule("unread all", [FakeAction(ActionType.mark_as_unread)])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(
            rp, "_matches", return_value=True
        ):
            count = rp.apply_rules(limit=5)

        self.assertEqual(count, 1)
        gmail.users.return_value.messages.return_value.modify.assert_called_once()
        args, kwargs = gmail.users.return_value.messages.return_value.modify.call_args
        self.assertIn("addLabelIds", kwargs["body"])

    def test_move_message_inbox(self):
        """move_message to Inbox should add INBOX label and not remove it"""
        email = make_email()
        store = FakeStore([email])
        gmail = MagicMock()
        gmail.users.return_value.messages.return_value.modify.return_value.execute.return_value = (
            {}
        )
        gmail.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            "labels": [{"id": "INBOX", "name": "INBOX"}]
        }

        rp = RulesProcessor(store, rules_file="dummy.json", gmail_service=gmail)
        rule = FakeRule("move all", [FakeAction(ActionType.move_message, "Inbox")])

        with patch.object(rp, "load_rules", return_value=[rule]), patch.object(
            rp, "_matches", return_value=True
        ):
            count = rp.apply_rules(limit=5)

        self.assertEqual(count, 1)
        gmail.users.return_value.messages.return_value.modify.assert_called_once()
        body = gmail.users.return_value.messages.return_value.modify.call_args.kwargs[
            "body"
        ]
        self.assertIn("INBOX", body["addLabelIds"])
        self.assertEqual(body["removeLabelIds"], [])


if __name__ == "__main__":
    unittest.main()
