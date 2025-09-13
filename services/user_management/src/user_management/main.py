from fastapi import FastAPI

app = FastAPI(title="User Management")

@app.get("/")
def health():
    return{"status": "ok"}

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt

app = FastAPI(title="User Management")

# ---- MODELE ----
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class PublicUser(BaseModel):
    email: EmailStr

# ---- "BAZA DE DATE" ÎN MEMORIE ----
USERS: list[dict] = []   # fiecare user = {"email": str, "password_hash": str}

@app.get("/")
def health():
    return {"status": "ok"}

# ---- /register ----
@app.post("/auth/register", response_model=PublicUser, status_code=201)
def register_user(data: RegisterRequest):
    # 1) verifică dacă email-ul există deja
    if any(u["email"].lower() == data.email.lower() for u in USERS):
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2) hash parolei
    pwd_hash = bcrypt.hash(data.password)

    # 3) salvează userul "în memorie"
    USERS.append({"email": data.email, "password_hash": pwd_hash})

    # 4) răspuns fără parolă
    return PublicUser(email=data.email)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt

app = FastAPI(title="User Management")

# ---- MODELE ----
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class PublicUser(BaseModel):
    email: EmailStr

# ---- "BAZA DE DATE" ÎN MEMORIE ----
USERS: list[dict] = []   # ex: {"email": "...", "password_hash": "..."}

@app.get("/")
def health():
    return {"status": "ok"}

# ---- /auth/register ----
@app.post("/auth/register", response_model=PublicUser, status_code=201)
def register_user(data: RegisterRequest):
    # 1) deja există?
    if any(u["email"].lower() == data.email.lower() for u in USERS):
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2) hash parolă
    pwd_hash = bcrypt.hash(data.password)

    # 3) salvez userul "în memorie"
    USERS.append({"email": data.email, "password_hash": pwd_hash})

    # 4) răspuns public (fără parolă)
    return PublicUser(email=data.email)

from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(title="User Management")

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

# ------------------ "BAZA DE DATE" ÎN MEMORIE ------------------
USERS: list[dict] = []   # fiecare: {"email": str, "password_hash": str}

# ------------------ JWT CONFIG ------------------
SECRET_KEY = "change-me-in-env"       # pentru demo; in prod => din env/secret manager
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MIN = 60         # 1 oră

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRES_MIN) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # găsește userul după email
    for u in USERS:
        if u["email"].lower() == email.lower():
            return u
    raise credentials_exc

# ------------------ ENDPOINTS ------------------
@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/auth/register", response_model=PublicUser, status_code=201)
def register_user(data: RegisterRequest):
    if any(u["email"].lower() == data.email.lower() for u in USERS):
        raise HTTPException(status_code=409, detail="Email already registered")
    pwd_hash = bcrypt.hash(data.password)
    USERS.append({"email": data.email, "password_hash": pwd_hash})
    return PublicUser(email=data.email)

@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    # caută userul
    user = next((u for u in USERS if u["email"].lower() == data.email.lower()), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # verifică parola
    if not bcrypt.verify(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # token JWT cu sub = email
    token = create_access_token({"sub": user["email"]})
    return TokenResponse(access_token=token)

@app.get("/auth/me", response_model=PublicUser)
def me(current_user: dict = Depends(get_current_user)):
    return PublicUser(email=current_user["email"])

from typing import Literal

# -------- Notifications --------
class NotificationRequest(BaseModel):
    to: EmailStr
    subject: str
    message: str
    channel: Literal["email", "console"] = "console"  # "console" = mock

def send_notification(n: NotificationRequest) -> None:
    """
    Mock sender: pentru demo trimitem în 'console'.
    Ulterior, aici poți pune integrarea reală (ex. AWS SES).
    """
    if n.channel == "console":
        print(f"[NOTIFY MOCK] to={n.to} subject={n.subject}\n{n.message}\n")
    elif n.channel == "email":
        # TODO: integrare reală (SES/SMTP). Deocamdată doar log:
        print(f"[EMAIL MOCK] to={n.to} subject={n.subject}\n{n.message}\n")
    else:
        raise HTTPException(status_code=400, detail="Unsupported channel")

