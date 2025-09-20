import requests
from .config import settings

def send_welcome_email(to_email: str) -> None:
    url = f"{settings.NOTIFICATIONS_BASE_URL}/notifications/send"
    payload = {
        "to": to_email,
        "subject": "Welcome!",
        "message": "Your account was created successfully. ",
        "channel": "ses"  
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] Failed to send welcome email to {to_email}: {e}")
