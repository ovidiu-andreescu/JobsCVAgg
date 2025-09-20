import boto3
from botocore.config import Config
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from .config import settings
from ..db.memory import save
from ..models.message import Message

import requests
from fastapi import HTTPException

def _send_sendgrid(to: str, subject: str, body: str) -> str:
    from .config import settings
    if not settings.SENDGRID_API_KEY or not settings.FROM_EMAIL:
        raise HTTPException(status_code=500, detail="SendGrid not configured")

    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": settings.FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    if r.status_code not in (200, 202):
        raise HTTPException(status_code=502, detail=f"SendGrid send failed: {r.text}")
    return "ok"


def _send_console(to: str, subject: str, body: str) -> str:
    msg_id = str(uuid4())
    print(f"[NOTIFY console] id={msg_id} to={to} subject={subject}\n{body}\n")
    save(Message(id=msg_id, to=to, subject=subject, body=body,
                 channel="console", status="sent", created_at=datetime.utcnow()))
    return msg_id

def _send_ses(to: str, subject: str, body: str) -> str:
    ses = boto3.client(
        "ses",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )
    try:
        ses.send_email(
            Source=settings.FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SES send failed: {exc}")

    msg_id = str(uuid4())
    save(Message(id=msg_id, to=to, subject=subject, body=body,
                 channel="ses", status="sent", created_at=datetime.utcnow()))
    return msg_id

def send_notification(*, to: str, subject: str, body: str, channel: str | None) -> str:
    provider = (channel or settings.NOTIFICATIONS_PROVIDER).lower()
    if provider == "console":
        return _send_console(to, subject, body)
    if provider == "ses":
        return _send_ses(to, subject, body)
    if provider == "sendgrid":
        return _send_sendgrid(to, subject, body)

    raise HTTPException(status_code=400, detail=f"Unsupported channel '{provider}'")

