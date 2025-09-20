from pydantic import BaseModel, EmailStr
from typing import Literal

class NotificationRequest(BaseModel):
    to: EmailStr
    subject: str
    message: str
    channel: Literal["ses", "console"] | None = None
