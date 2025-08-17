from typing import Optional

from gmail_helper.api.email_service.models import EmailResponse, EmailsListResponse
from gmail_helper.common.contracts.emails_interface import EmailsInterface


class EmailService:
    """
    Application service for emails. Depends on EmailsInterface (contract).
    """

    def __init__(self, store: EmailsInterface):
        self.store = store

    def get_last_emails(self, n: int = 10) -> EmailsListResponse:
        rows = self.store.get_last_n_emails(n)
        emails = [EmailResponse(**row) for row in rows]
        return EmailsListResponse(emails=emails)

    def get_email_by_id(self, email_id: str) -> Optional[EmailResponse]:
        row = self.store.get_email_by_id(email_id)
        return EmailResponse(**row) if row else None
