from typing import List
from ..models.message import Message

_OUTBOX: List[Message] = []

def save(msg: Message) -> None:
    _OUTBOX.append(msg)

def all_messages() -> list[dict]:
    return [m.__dict__ for m in _OUTBOX]

def clear() -> None:
    _OUTBOX.clear()
