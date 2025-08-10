import unittest
from unittest.mock import MagicMock, patch

from gmail_helper.api.email_fetcher.service import GmailFetcherService
from gmail_helper.api.email_fetcher.store import EmailsStore


class TestGmailFetcherService(unittest.TestCase):

    def setUp(self):
        self.mock_store = MagicMock(spec=EmailsStore)
        patcher = patch.object(
            GmailFetcherService, "authenticate", return_value=MagicMock()
        )
        self.mock_authenticate = patcher.start()
        self.addCleanup(patcher.stop)

        self.service = GmailFetcherService(emails_store=self.mock_store)

    def test_init_calls_init_db_and_authenticate(self):
        self.mock_store.init_db.assert_called_once()
        self.mock_authenticate.assert_called_once()

    def test_parse_mail_happy_path(self):
        mail = {
            "id": "123",
            "threadId": "abc",
            "snippet": "hello",
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Subject", "value": "Test"},
                    {"name": "Date", "value": "Fri, 08 Aug 2025 16:35:27 +0530"},
                ]
            },
        }

        with patch(
            "gmail_helper.common.utils.parse_email_date_format",
            return_value="2025-08-08T16:35:27+05:30",
        ):
            result = GmailFetcherService.parse_mail(mail)

        self.assertEqual(result[2], "alice@example.com")
        self.assertEqual(result[3], "Test")
        self.assertIn("2025-08-08", result[5])

    def test_parse_mail_with_invalid_date(self):
        mail = {
            "id": "123",
            "threadId": "abc",
            "snippet": "hello",
            "payload": {"headers": [{"name": "Date", "value": "invalid"}]},
        }

        with patch(
            "gmail_helper.common.utils.parse_email_date_format", side_effect=ValueError
        ):
            result = GmailFetcherService.parse_mail(mail)

        self.assertEqual(result[5], "invalid")  # fallback to raw date

    def test_fetch_mails(self):
        mails = [{"id": "1"}, {"id": "2"}]
        self.service.service.users().messages().list().execute.return_value = {
            "messages": mails
        }
        result = self.service.fetch_mails(max_results=5)
        self.assertEqual(result, mails)
        self.service.service.users().messages().list.assert_called_with(
            userId="me", labelIds=["INBOX"], maxResults=5
        )

    def test_fetch_full_mail_for_id(self):
        mail = {"id": "123"}
        self.service.service.users().messages().get().execute.return_value = mail
        result = self.service.fetch_full_mail_for_id("123")
        self.assertEqual(result, mail)
        self.service.service.users().messages().get.assert_called_with(
            userId="me", id="123", format="metadata"
        )

    def test_orchestrate_stores_emails(self):
        mails = [{"id": "1"}]
        full_mail = {
            "id": "1",
            "threadId": "t1",
            "payload": {"headers": []},
            "snippet": "test",
        }

        self.service.fetch_mails = MagicMock(return_value=mails)
        self.service.fetch_full_mail_for_id = MagicMock(return_value=full_mail)
        with patch.object(
            GmailFetcherService,
            "parse_mail",
            return_value=("1", "t1", "from", "subject", "snippet", "date"),
        ):
            self.service.orchestrate()

        self.mock_store.insert_email.assert_called_once()
