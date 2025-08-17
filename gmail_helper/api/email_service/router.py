from typing import Optional

from gmail_helper.api.email_service.models import EmailResponse, EmailsListResponse
from gmail_helper.api.email_service.rules_processor import RulesProcessor
from gmail_helper.api.email_service.service import EmailService
from gmail_helper.common.utils.api_framework import api_get, api_router


@api_router(prefix="/emails", tags=["Emails"])
class EmailRouter:
    """
    Thin router (controller) — only orchestration & IO concerns.
    Service depends on EmailsInterface (contract).
    """

    def __init__(self, email_service: EmailService, rules_service: RulesProcessor = None):
        self.email_service = email_service
        self.rules_service = rules_service

    @api_get("/last", response_model=EmailsListResponse, summary="Get last N stored emails")
    def last(self, n: int = 10):
        return self.email_service.get_last_emails(n)

    @api_get(
        "/{email_id}",
        response_model=Optional[EmailResponse],
        summary="Get a single email by ID",
    )
    def get_by_id(self, email_id: str):
        return self.email_service.get_email_by_id(email_id)

    @api_get("/rules", response_model=dict, summary="List Rules")
    def list_rules(self, limit=10):
        return self.rules_service.load_rules()[:limit]
