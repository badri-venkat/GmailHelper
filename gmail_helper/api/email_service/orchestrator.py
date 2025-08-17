import os

from gmail_helper.common.utils.logger import get_logger
from gmail_helper.stores.emails_store import EmailsStore

LOG = get_logger(__name__)


from typing import List, Optional

from gmail_helper.api.email_service.rules_processor import RulesProcessor
from gmail_helper.common.config import config
from gmail_helper.common.contracts.emails_interface import EmailsInterface
from gmail_helper.common.services.gmail_service import GmailClient
from gmail_helper.common.utils.dateutils import parse_rfc2822_to_iso
from gmail_helper.common.utils.logger import get_logger

LOG = get_logger(__name__)


class GmailOrchestrator:
    """
    Fetches emails from Gmail and stores them in SQLite.
    Optionally runs rules and applies actions using GmailClient.
    """

    def __init__(
        self,
        store: EmailsInterface,
        gmail_client: Optional[GmailClient] = None,
    ):
        self.store = store
        self.gmail = gmail_client or GmailClient()

    def fetch_and_store(
        self,
        max_results: int = None,
        label_ids: Optional[List[str]] = None,
    ) -> int:
        max_results = max_results or config.FETCH_BATCH_SIZE
        label_ids = label_ids or list(config.DEFAULT_LABELS)

        LOG.info("Fetching up to %d messages with labels=%s...", max_results, label_ids)
        msgs = self.gmail.list_messages(label_ids=label_ids, max_results=max_results)
        LOG.info("Found %d messages", len(msgs))

        stored = 0
        for item in msgs:
            full = self.gmail.get_message_metadata(item["id"])
            headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}

            email = {
                "id": full.get("id", ""),
                "thread_id": full.get("threadId", ""),
                "sender": headers.get("From", "") or "",
                "subject": headers.get("Subject", "") or "",
                "snippet": full.get("snippet", "") or "",
                "received_datetime": parse_rfc2822_to_iso(headers.get("Date", "")),
            }
            self.store.insert_email(email)
            stored += 1

        LOG.info("Stored %d messages into DB at %s", stored, config.DB_PATH)
        return stored

    def run_rules(self, rules_file: Optional[str] = None, limit: int = 20) -> int:
        rp = RulesProcessor(
            store=self.store,
            rules_file=rules_file or config.RULES_FILE,
            gmail_client=self.gmail,  # pass the shared client
        )
        return rp.apply_rules(limit=limit)


if __name__ == "__main__":
    orch = GmailOrchestrator()
    orch.fetch_and_store()
    if os.path.exists(config.RULES_FILE):
        orch.run_rules()
