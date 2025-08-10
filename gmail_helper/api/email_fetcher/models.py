from datetime import datetime

from pydantic import BaseModel


class Email(BaseModel):
    id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str
    received_datetime: datetime
