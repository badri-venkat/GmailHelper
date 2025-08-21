import os
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_helper.common.utils.logger import get_logger

LOG = get_logger(__name__)


class GmailClient:
    """
    Thin wrapper around the Gmail API (googleapiclient).
    Handles auth and common operations we need.
    """

    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        scopes: list[str],
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self._service = None

    def service(self):
        """Return authenticated gmail service (lazy)."""
        if self._service is None:
            self._service = self._authenticate()
        return self._service

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                LOG.info("Refreshing Gmail token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError("Gmail credentials file not found at %s" % self.credentials_file)
                LOG.info("Starting Gmail OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        LOG.info("Gmail auth OK")
        return build("gmail", "v1", credentials=creds)

    def list_messages(
        self,
        user_id: str = "me",
        label_ids: Optional[List[str]] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict]:
        res = (
            self.service()
            .users()
            .messages()
            .list(userId=user_id, labelIds=label_ids or [], maxResults=max_results)
            .execute()
        )
        return res.get("messages", []) or []

    def get_message_metadata(self, msg_id: str, user_id: str = "me") -> Dict:
        return self.service().users().messages().get(userId=user_id, id=msg_id, format="metadata").execute()

    def modify_message(
        self,
        msg_id: str,
        user_id: str = "me",
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> Dict:
        body = {
            "addLabelIds": add_label_ids or [],
            "removeLabelIds": remove_label_ids or [],
        }
        return self.service().users().messages().modify(userId=user_id, id=msg_id, body=body).execute()

    def list_labels(self, user_id: str = "me") -> List[Dict]:
        res = self.service().users().labels().list(userId=user_id).execute()
        return res.get("labels", []) or []

    def create_label(self, name: str, user_id: str = "me") -> Dict:
        body = {
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        return self.service().users().labels().create(userId=user_id, body=body).execute()
