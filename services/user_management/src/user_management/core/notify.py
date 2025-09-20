import os
import requests

NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://127.0.0.1:5001/notifications")
NOTIF_CHANNEL = os.getenv("NOTIF_CHANNEL", "console")

def send_verification_email(to: str, verify_url: str) -> None:
    payload = {
        "to": to,
        "subject": "Verifică-ți contul - JobsCVAgg",
        "message": f"Bună!\nDă click pentru a-ți verifica emailul:\n{verify_url}\n",
        "channel": NOTIF_CHANNEL,
    }
    try:
        r = requests.post(f"{NOTIFICATIONS_URL}/send", json=payload, timeout=5)
        r.raise_for_status()
    except Exception as e:
        print("!!! Failed to send notification:", e)
