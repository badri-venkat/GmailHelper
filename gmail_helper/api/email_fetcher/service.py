import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_helper.api.email_fetcher.store import EmailsStore
from gmail_helper.common.utils import parse_email_date_format


class GmailFetcherService:
    def __init__(
        self,
        emails_store: EmailsStore,
        credentials_file="/Users/badrinathv/Personal/GmailHelper/.credentials.json",
        token_file=".token.json",
    ):
        self.scopes = ["https://www.googleapis.com/auth/gmail.modify"]
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.emails_store = emails_store
        self.emails_store.init_db()
        self.service = self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    @staticmethod
    def parse_mail(mail):
        headers = mail.get("payload", {}).get("headers", [])
        header_dict = {h["name"]: h["value"] for h in headers}
        sender = header_dict.get("From", "")
        subject = header_dict.get("Subject", "")
        snippet = mail.get("snippet", "")
        date = header_dict.get("Date", "")

        try:
            parsed_date = str(parse_email_date_format(date))
        except Exception:
            parsed_date = date

        return (
            mail["id"],
            mail["threadId"],
            sender,
            subject,
            snippet,
            parsed_date,
        )

    def fetch_mails(self, max_results: int = 20) -> list:
        results = (
            self.service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )

        return results.get("messages", [])

    def fetch_full_mail_for_id(self, mail_id: str) -> dict:
        full_mail = (
            self.service.users()
            .messages()
            .get(userId="me", id=mail_id, format="metadata")
            .execute()
        )
        return full_mail

    def orchestrate(self):
        mails = self.fetch_mails(max_results=10)
        if not mails:
            print("No messages found.")
            return

        print(f"Found {len(mails)} mails")
        for mail in mails:
            full_mail = self.fetch_full_mail_for_id(mail["id"])
            email_data = self.parse_mail(full_mail)
            self.emails_store.insert_email(email_data)
            print(f"Stored email: {email_data[3]} from {email_data[2]}")
