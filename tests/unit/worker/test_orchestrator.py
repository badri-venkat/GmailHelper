import unittest
from unittest.mock import MagicMock, patch

from gmail_helper.worker.orchestrator import GmailOrchestrator


class TestGmailOrchestrator(unittest.TestCase):
    def setUp(self):

        self.patcher = patch.object(GmailOrchestrator, "_authenticate")
        self.mock_auth = self.patcher.start()

        self.fake_service = MagicMock()
        self.mock_auth.return_value = self.fake_service

        # Fake store
        self.fake_store = MagicMock()

        self.orch = GmailOrchestrator(store=self.fake_store)

    def tearDown(self):
        self.patcher.stop()

    def test_fetch_and_store_no_messages(self):
        """If Gmail returns no messages, nothing should be stored"""
        self.fake_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": []
        }

        count = self.orch.fetch_and_store(max_results=5)
        self.assertEqual(count, 0)
        self.fake_store.insert_email.assert_not_called()

    def test_fetch_and_store_with_messages(self):
        """Fetched messages should be transformed and inserted into store"""
        # list returns one message
        self.fake_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [{"id": "abc"}]
        }
        # get returns details
        self.fake_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "abc",
            "threadId": "t1",
            "snippet": "Hello",
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
        self.fake_store.insert_email.assert_called_once()
        inserted_email = self.fake_store.insert_email.call_args[0][0]
        self.assertEqual(inserted_email["id"], "abc")
        self.assertEqual(inserted_email["subject"], "Hi")
        self.assertEqual(inserted_email["sender"], "sender@example.com")

    def test_run_rules_delegates_to_rulesprocessor(self):
        """run_rules should construct RulesProcessor and call apply_rules"""
        with patch("gmail_helper.worker.orchestrator.RulesProcessor") as MockRP:
            rp_instance = MockRP.return_value
            rp_instance.apply_rules.return_value = 42

            result = self.orch.run_rules(rules_file="rules.json", limit=5)

        MockRP.assert_called_once_with(
            self.fake_store, rules_file="rules.json", gmail_service=self.fake_service
        )
        rp_instance.apply_rules.assert_called_once_with(limit=5)
        self.assertEqual(result, 42)


if __name__ == "__main__":
    unittest.main()
