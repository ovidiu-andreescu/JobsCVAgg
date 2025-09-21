from typing import Set, Optional

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
    class UserInDB(BaseModel):
        email: EmailStr
        password_hash: str
        is_verified: bool = False
        verify_token: Optional[str] = None

