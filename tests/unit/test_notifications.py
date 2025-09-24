from fastapi.testclient import TestClient
from notifications.app import app

client = TestClient(app)

def test_health_notif():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_send_console_and_outbox():
    # curăță outbox
    client.delete("/notifications/_debug/outbox")

    payload = {
        "to": "notify@example.com",
        "subject": "Hi",
        "message": "Body",
        "channel": "console"
    }
    r = client.post("/notifications/send", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "sent"
    assert body["channel"] == "console"
    assert body["id"]

    # verifică outbox
    r = client.get("/notifications/_debug/outbox")
    assert r.status_code == 200
    out = r.json()
    assert len(out) == 1
    assert out[0]["to"] == "notify@example.com"
