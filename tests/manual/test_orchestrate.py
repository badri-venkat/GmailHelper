import unittest

from gmail_helper.api.email_fetcher.service import GmailFetcherService
from gmail_helper.api.email_fetcher.store import EmailsStore


class TestEmailFetch(unittest.TestCase):
    def setUp(self):
        self.store = EmailsStore(db_name="emails.db")
        self.service = GmailFetcherService(self.store)

    def test_store_fetch(self):
        for row in self.store.select_most_recent_k_mails(10):
            print(row)

    def test_gmail_fetch(self):
        self.service.orchestrate()
