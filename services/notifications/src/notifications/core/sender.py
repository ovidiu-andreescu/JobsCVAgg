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
        headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                 "Content-Type": "application/json"},
        json=payload, timeout=15
    )
    if r.status_code not in (200, 202):
        raise HTTPException(status_code=502, detail=f"SendGrid error: {r.text}")
    return f"sendgrid-{uuid4()}"


def _send_console(to: str, subject: str, body: str) -> str:
    return f"console-{uuid4()}"


def _send_ses(to: str, subject: str, body: str) -> str:
    if not settings.SES_FROM_EMAIL:
        raise HTTPException(status_code=500, detail="SES not configured")
    ses = boto3.client("ses", config=Config(retries={"max_attempts": 3}))
    ses.send_email(
        Source=settings.SES_FROM_EMAIL,
        Destination={"ToAddresses": [to]},
        Message={"Subject": {"Data": subject}, "Body": {"Text": {"Data": body}}}
    )
    return f"ses-{uuid4()}"

def send_notification(to: str, subject: str, body: str, channel: str | None = None) -> str:
    provider = (channel or settings.NOTIFICATIONS_PROVIDER).lower()
    if provider == "console":
        msg_id = _send_console(to, subject, body)
    elif provider == "sendgrid":
        msg_id = _send_sendgrid(to, subject, body)
    elif provider == "ses":
        msg_id = _send_ses(to, subject, body)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown channel '{provider}'")

    save(Message(
        id=msg_id, to=to, subject=subject, body=body,
        channel=provider, status="sent", created_at=datetime.utcnow()
    ))
    return msg_id