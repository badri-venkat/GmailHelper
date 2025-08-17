import unittest
from unittest.mock import MagicMock, patch

from gmail_helper.worker.orchestrator import GmailOrchestrator


class TestGmailOrchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_gmail = MagicMock()
        self.mock_store = MagicMock()
        self.orch = GmailOrchestrator(
            store=self.mock_store, gmail_client=self.mock_gmail
        )

    def test_fetch_and_store_no_messages(self):
        """If Gmail returns no messages, nothing is inserted"""
        self.mock_gmail.list_messages.return_value = []

        count = self.orch.fetch_and_store(max_results=5, label_ids=["INBOX"])

        self.assertEqual(count, 0)
        self.mock_store.insert_email.assert_not_called()
        self.mock_gmail.list_messages.assert_called_once_with(
            label_ids=["INBOX"], max_results=5
        )

    def test_fetch_and_store_with_messages(self):
        """Fetched messages should be transformed and stored"""
        # list_messages returns one message
        self.mock_gmail.list_messages.return_value = [{"id": "m1"}]
        # get_message_metadata returns full metadata
        self.mock_gmail.get_message_metadata.return_value = {
            "id": "m1",
            "threadId": "t1",
            "snippet": "Hello there",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Hi"},
                    {"name": "Date", "value": "Mon, 12 Aug 2024 10:00:00 +0000"},
                ]
            },
        }

        with patch(
            "gmail_helper.worker.orchestrator.parse_rfc2822_to_iso",
            return_value="2024-08-12T10:00:00Z",
        ):
            count = self.orch.fetch_and_store(max_results=1)

        self.assertEqual(count, 1)
        self.mock_store.insert_email.assert_called_once()
        inserted = self.mock_store.insert_email.call_args[0][0]
        self.assertEqual(inserted["id"], "m1")
        self.assertEqual(inserted["thread_id"], "t1")
        self.assertEqual(inserted["sender"], "sender@example.com")
        self.assertEqual(inserted["subject"], "Hi")
        self.assertEqual(inserted["received_datetime"], "2024-08-12T10:00:00Z")

    def test_run_rules_calls_rulesprocessor(self):
        """run_rules should delegate to RulesProcessor"""
        with patch("gmail_helper.worker.orchestrator.RulesProcessor") as MockRP:
            rp_instance = MockRP.return_value
            rp_instance.apply_rules.return_value = 99

            result = self.orch.run_rules(rules_file="rules.json", limit=7)

        # Check RulesProcessor was constructed properly
        MockRP.assert_called_once_with(
            store=self.mock_store,
            rules_file="rules.json",
            gmail_client=self.mock_gmail,
        )
        rp_instance.apply_rules.assert_called_once_with(limit=7)
        self.assertEqual(result, 99)
