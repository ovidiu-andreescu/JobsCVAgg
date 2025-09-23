from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, ValidationError
from passlib.hash import bcrypt
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from user_management.schemas.auth import UserInDB
from user_management.db.dynamodb import create_user, get_user_by_email
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from uuid import uuid4


# ------------------ MODELE ------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PublicUser(BaseModel):
    email: EmailStr

class CurrentUser(BaseModel):
    email: EmailStr

class DebugVerifyIn(BaseModel):
    email: EmailStr | None = None
    token: str | None = None

# ------------------ "BAZA DE DATE" ÎN MEMORIE ------------------
# fiecare user: {"email": str, "password_hash": str}
USERS: List[Dict[str, str]] = []


# ------------------ JWT CONFIG ------------------
SECRET_KEY = os.environ['JWT_SECRET_KEY']
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MIN = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
bearer = HTTPBearer(auto_error=True)

def create_access_token(subject: str, minutes: int = ACCESS_TOKEN_EXPIRES_MIN) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    payload =  jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["exp", "iat", "sub", "type"]},
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> CurrentUser:
    token = creds.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Not an access token")

        email = payload["sub"]
        user = get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.get("is_verified", False):
            raise HTTPException(status_code=403, detail="Email not verified")

        return CurrentUser(email=email)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

