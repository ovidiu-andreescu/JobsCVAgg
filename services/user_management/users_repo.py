from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import String, Boolean
from .db import Base, engine, SessionLocal
from passlib.context import CryptContext
import uuid

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verify_token: Mapped[str | None] = mapped_column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def hash_password(x: str) -> str: return pwd.hash(x)
def verify_password(x: str, h: str) -> bool: return pwd.verify(x, h)

class UsersRepo:
    def __init__(self, db: Session): self.db = db
    def by_email(self, email: str): return self.db.query(User).filter(User.email==email).first()
    def by_token(self, token: str): return self.db.query(User).filter(User.verify_token==token).first()
    def create(self, email: str, password_hash: str, token: str):
        u = User(email=email, password_hash=password_hash, verify_token=token)
        self.db.add(u); self.db.commit(); self.db.refresh(u); return u
    def verify(self, user_id: str):
        u = self.db.get(User, user_id)
        if u: u.is_verified=True; u.verify_token=None; self.db.commit()
