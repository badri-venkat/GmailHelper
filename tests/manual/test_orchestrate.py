import os
import unittest

from gmail_helper.api.containers import ApiContainer
from gmail_helper.common.config import config


class TestEmailFetch(unittest.TestCase):
    def setUp(self):
        self.container = ApiContainer()

    def test_run_mail_collection(self):
        """Test #1 to oauth and fetch recent 20 mails using GmailApi"""
        orchestrator = self.container.orchestrator()
        orchestrator.fetch_and_store()

    def test_run_rules(self):
        """Test #2 to apply rules configured in rules.json"""
        orchestrator = self.container.orchestrator()
        if os.path.exists(config.RULES_FILE):
            orchestrator.run_rules()
