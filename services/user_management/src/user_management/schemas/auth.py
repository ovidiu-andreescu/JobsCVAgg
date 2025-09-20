from typing import Set

from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PublicUser(BaseModel):
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInDB(BaseModel):
    email: EmailStr
    password_hash: str
    keywords: Set[str] = set()