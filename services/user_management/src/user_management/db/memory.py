from typing import Optional, List
from ..models.user import User

USERS: List[User] = []  # înlocuibil ulterior cu DynamoDB

def get_by_email(email: str) -> Optional[User]:
    email = email.lower()
    return next((u for u in USERS if u.email.lower() == email), None)

def add_user(u: User) -> None:
    USERS.append(u)
