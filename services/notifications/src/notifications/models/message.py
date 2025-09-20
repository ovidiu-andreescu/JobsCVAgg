from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    id: str
    to: str
    subject: str
    body: str
    channel: str
    status: str
    created_at: datetime
