import unittest
from unittest.mock import Mock, patch

from freezegun import freeze_time

from gmail_helper.api.email_service.orchestrator import GmailOrchestrator


class TestGmailOrchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_store = Mock()
        self.mock_gmail = Mock()
        self.mock_rules = Mock()

        self.orch = GmailOrchestrator(
            store=self.mock_store,
            rules_processor=self.mock_rules,
            gmail_client=self.mock_gmail,
        )

    def test_fetch_and_store_no_messages(self):
        self.mock_gmail.list_messages.return_value = []

        count = self.orch.fetch_and_store(max_results=5, label_ids=["INBOX"])

        self.assertEqual(count, 0)
        self.mock_store.insert_email.assert_not_called()
        self.mock_gmail.list_messages.assert_called_once_with(label_ids=["INBOX"], max_results=5)

    @freeze_time("2024-08-12 10:00:00")
    def test_fetch_and_store_with_message(self):
        self.mock_gmail.list_messages.return_value = [{"id": "m1"}]
        self.mock_gmail.get_message_metadata.return_value = {
            "id": "m1",
            "threadId": "t1",
            "snippet": "Hello snippet",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Hi"},
                    {"name": "Date", "value": "Mon, 12 Aug 2024 10:00:00 +0000"},
                ]
            },
        }

        # Patch parse_rfc2822_to_iso to use the frozen time context
        with patch(
            "gmail_helper.api.email_service.orchestrator.parse_rfc2822_to_iso", return_value="2024-08-12T10:00:00Z"
        ):
            count = self.orch.fetch_and_store(max_results=1)

        self.assertEqual(count, 1)
        self.mock_store.insert_email.assert_called_once()
        email_arg = self.mock_store.insert_email.call_args[0][0]
        self.assertEqual(email_arg["id"], "m1")
        self.assertEqual(email_arg["thread_id"], "t1")
        self.assertEqual(email_arg["sender"], "sender@example.com")
        self.assertEqual(email_arg["subject"], "Hi")
        self.assertEqual(email_arg["received_datetime"], "2024-08-12T10:00:00Z")

    def test_run_rules_delegates(self):
        self.mock_rules.apply_rules.return_value = 42

        result = self.orch.run_rules(limit=7)

        self.assertEqual(result, 42)
        self.mock_rules.apply_rules.assert_called_once_with(limit=7)
