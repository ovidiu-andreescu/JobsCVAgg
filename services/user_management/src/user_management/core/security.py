from datetime import datetime, timedelta
from jose import jwt
from passlib.hash import bcrypt
from .config import settings

def hash_password(raw: str) -> str:
    return bcrypt.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return bcrypt.verify(raw, hashed)

def create_access_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MIN),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])
