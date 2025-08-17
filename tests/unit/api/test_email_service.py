import unittest
from unittest.mock import MagicMock

from gmail_helper.api.email_service.models import (EmailResponse,
                                                   EmailsListResponse)
from gmail_helper.api.email_service.service import EmailService


class TestEmailService(unittest.TestCase):
    def setUp(self):
        self.mock_store = MagicMock()
        self.service = EmailService(self.mock_store)

    def test_get_last_emails_returns_wrapped_list(self):
        # Mock store returns list of dicts
        self.mock_store.get_last_n_emails.return_value = [
            {
                "id": "1",
                "thread_id": "t1",
                "sender": "a@example.com",
                "subject": "Hello",
                "snippet": "hi",
                "received_datetime": "2024-08-12T10:00:00Z",
            },
            {
                "id": "2",
                "thread_id": "t2",
                "sender": "b@example.com",
                "subject": "World",
                "snippet": "hey",
                "received_datetime": "2024-08-13T10:00:00Z",
            },
        ]

        resp = self.service.get_last_emails(2)

        self.mock_store.get_last_n_emails.assert_called_once_with(2)
        self.assertIsInstance(resp, EmailsListResponse)
        self.assertEqual(len(resp.emails), 2)
        self.assertIsInstance(resp.emails[0], EmailResponse)
        self.assertEqual(resp.emails[0].id, "1")
        self.assertEqual(resp.emails[1].subject, "World")

    def test_get_email_by_id_found(self):
        self.mock_store.get_email_by_id.return_value = {
            "id": "123",
            "thread_id": "t123",
            "sender": "c@example.com",
            "subject": "Test",
            "snippet": "body",
            "received_datetime": "2024-08-14T10:00:00Z",
        }

        resp = self.service.get_email_by_id("123")

        self.mock_store.get_email_by_id.assert_called_once_with("123")
        self.assertIsInstance(resp, EmailResponse)
        self.assertEqual(resp.id, "123")
        self.assertEqual(resp.subject, "Test")

    def test_get_email_by_id_not_found(self):
        self.mock_store.get_email_by_id.return_value = None

        resp = self.service.get_email_by_id("does-not-exist")

        self.mock_store.get_email_by_id.assert_called_once_with("does-not-exist")
        self.assertIsNone(resp)

