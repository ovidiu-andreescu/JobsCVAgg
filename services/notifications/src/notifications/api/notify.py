from fastapi import APIRouter
from ..schemas.notify import NotificationRequest
from ..core.sender import send_notification
from ..db.memory import all_messages, clear as clear_outbox
from ..core.config import settings

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/send")
def send(n: NotificationRequest):
    msg_id = send_notification(to=n.to, subject=n.subject, body=n.message, channel=n.channel)
    return {"id": msg_id, "status": "sent", "channel": (n.channel or settings.NOTIFICATIONS_PROVIDER)}


@router.get("/_debug/outbox")
def outbox():
    return all_messages()

@router.delete("/_debug/outbox")
def outbox_clear():
    clear_outbox()
    return {"cleared": True}
