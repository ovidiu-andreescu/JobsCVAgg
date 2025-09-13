from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
import requests
import os
from uuid import uuid4

from ..db.sqlite import (
    create_user,
    get_user_by_email,
    get_user_by_token,
    mark_verified,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# config din .env (sau valori default pt. local)
NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://127.0.0.1:5001/notifications")
NOTIF_CHANNEL     = os.getenv("NOTIF_CHANNEL", "console")   # "sendgrid" | "console"
PUBLIC_BASE_URL   = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:5000")

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(p: RegisterIn):
    email = p.email.strip().lower()
    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")

    password_hash = bcrypt.hash(p.password)
    token = str(uuid4())

    try:
        create_user(email=email, password_hash=password_hash, verify_token=token)
    except ValueError:
        raise HTTPException(status_code=409, detail="Email already registered")

    # trimite email cu link de verificare
    verify_url = f"{PUBLIC_BASE_URL}/auth/verify?token={token}"
    body = f"""Buna!

Ti-ai creat cont pe JobsCVAgg.
Te rog verifica adresa de email dand click pe linkul de mai jos:

{verify_url}

Daca nu tu ai initiat, ignora acest mesaj.
"""
    try:
        requests.post(
            f"{NOTIFICATIONS_URL}/send",
            json={
                "to": email,
                "subject": "Verifica-ti contul - JobsCVAgg",
                "message": body,
                "channel": NOTIF_CHANNEL,
            },
            timeout=12,
        )
    except Exception as e:
        # nu blocam inregistrarea daca emailul esueaza
        print(f"[WARN] notification failed: {e}")

    return {"ok": True}

@router.get("/verify")
def verify(token: str):
    u = get_user_by_token(token)
    if not u:
        raise HTTPException(status_code=400, detail="Invalid token")
    if u["is_verified"]:
        return {"verified": True, "message": "Already verified"}
    mark_verified(u["id"])
    return {"verified": True}

@router.post("/login")
def login(p: LoginIn):
    email = p.email.strip().lower()
    u = get_user_by_email(email)
    if not u or not bcrypt.verify(p.password, u["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not u["is_verified"]:
        raise HTTPException(status_code=403, detail="Email not verified")
    return {"ok": True, "email": email}

from fastapi import HTTPException

@router.get("/_debug/verify_link")
def debug_verify_link(email: str):
    email = email.strip().lower()
    u = get_user_by_email(email)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    if u["is_verified"]:
        return {"verified": True, "url": None}
    token = u["verify_token"]
    return {
        "verified": False,
        "url": f"{PUBLIC_BASE_URL}/auth/verify?token={token}" if token else None
    }
