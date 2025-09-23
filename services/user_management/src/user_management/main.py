from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, ValidationError
from passlib.hash import bcrypt  
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

from user_management.schemas.auth import UserInDB
from user_management.db.dynamodb import create_user, get_user_by_email

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

# ------------------ "BAZA DE DATE" ÎN MEMORIE ------------------
# fiecare user: {"email": str, "password_hash": str}
USERS: List[Dict[str, str]] = []


# ------------------ JWT CONFIG ------------------
SECRET_KEY = os.environ['JWT_SECRET_KEY']
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MIN = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(subject: str, expires_minutes: int = ACCESS_TOKEN_EXPIRES_MIN) -> str:
    to_encode = {
        "sub": subject,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if not email:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = get_user_by_email(email)
    if not user:
        raise credentials_exc
    try:
        return CurrentUser(email=user["email"] if isinstance(user, dict) else user.email)
    except ValidationError:
        raise credentials_exc


# ------------------ ENDPOINTS ------------------
@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=PublicUser, status_code=201)
def register_user(data: RegisterRequest):
    if get_user_by_email(data.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    pwd_hash = bcrypt.hash(data.password)
    verify_token = str(uuid4())

    new_user = UserInDB(
        email=data.email,
        password_hash=pwd_hash,
        is_verified=False,
        verify_token=verify_token
    )

    try:
        create_user(new_user)
    except ValueError:
        raise HTTPException(status_code=409, detail="Email already registered")

    return PublicUser(email=data.email)


@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or not bcrypt.verify(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user["email"])
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=PublicUser)
def me(current_user: CurrentUser = Depends(get_current_user)):
    return PublicUser(email=current_user.email)
