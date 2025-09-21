# from fastapi.testclient import TestClient
# from uuid import uuid4
#
# from services.user_management.src.user_management.app import app
# from services.user_management.src.user_management.db.sqlite import get_user_by_email
#
# client = TestClient(app)
#
#
# def test_health_um():
#     r = client.get("/")
#     assert r.status_code == 200
#     assert r.json() == {"status": "ok"}
#
#
# def test_register_verify_login_flow():
#     # folosim un email unic ca să nu lovim "Email already registered"
#     email = f"t_{uuid4().hex[:8]}@example.com"
#     password = "1234"
#
#     # 1) register
#     r = client.post("/auth/register", json={"email": email, "password": password})
#     assert r.status_code == 200
#     assert r.json().get("ok") is True
#
#     # 2) verify (citit tokenul din DB, apoi apelam /auth/verify)
#     user = get_user_by_email(email)
#     assert user is not None
#     token = user["verify_token"]
#     assert token is not None
#
#     r = client.get(f"/auth/verify?token={token}")
#     assert r.status_code == 200
#     assert r.json().get("verified") is True
#
#     # 3) login
#     r = client.post("/auth/login", json={"email": email, "password": password})
#     assert r.status_code == 200
#     data = r.json()
#     assert data.get("ok") is True
#     assert data.get("email") == email
