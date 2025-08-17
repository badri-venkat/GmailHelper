import os
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_helper.common.config import config
from gmail_helper.common.utils.dateutils import parse_rfc2822_to_iso
from gmail_helper.common.utils.logger import get_logger
from gmail_helper.worker.emails_store import EmailsStore
from gmail_helper.worker.rules_processor import RulesProcessor

LOG = get_logger(__name__)


class GmailOrchestrator:
    """
    Fetches emails from Gmail (read-only) and stores them in SQLite.
    Optionally runs rules from rules.json and logs actions.
    """

    def __init__(self, store: Optional[EmailsStore] = None):
        self.store = store or EmailsStore(db_path=config.DB_PATH)
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(config.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(
                config.TOKEN_FILE, config.SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                LOG.info("Refreshing Gmail token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(config.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        "Gmail credentials file not found at %s"
                        % config.CREDENTIALS_FILE
                    )
                LOG.info("Starting Gmail OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.CREDENTIALS_FILE, config.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(config.TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        LOG.info("Gmail auth OK")
        return build("gmail", "v1", credentials=creds)

    def fetch_and_store(
        self,
        max_results: int = None,
        label_ids: Optional[List[str]] = None,
    ) -> int:
        max_results = max_results or config.FETCH_BATCH_SIZE
        label_ids = label_ids or list(config.DEFAULT_LABELS)

        LOG.info("Fetching up to %d messages with labels=%s...", max_results, label_ids)
        res = (
            self.service.users()
            .messages()
            .list(userId="me", labelIds=label_ids, maxResults=max_results)
            .execute()
        )
        msgs = res.get("messages", [])
        LOG.info("Found %d messages", len(msgs))

        stored = 0
        for item in msgs:
            full = (
                self.service.users()
                .messages()
                .get(userId="me", id=item["id"], format="metadata")
                .execute()
            )
            headers = {
                h["name"]: h["value"]
                for h in full.get("payload", {}).get("headers", [])
            }

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
        rp = RulesProcessor(self.store, rules_file=rules_file or config.RULES_FILE)
        return rp.apply_rules(limit=limit)


if __name__ == "__main__":
    orch = GmailOrchestrator()
    if os.path.exists(config.RULES_FILE):
        orch.run_rules()
