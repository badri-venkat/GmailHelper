from typing import List

from pydantic import BaseModel


class EmailResponse(BaseModel):
    id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str
    received_datetime: str


class EmailsListResponse(BaseModel):
    emails: List[EmailResponse]
