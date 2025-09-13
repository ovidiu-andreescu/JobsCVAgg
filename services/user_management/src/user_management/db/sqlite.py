import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "users.db"

def _connect():
    return sqlite3.connect(DB_PATH)

# Inițializează baza + tabelul users (cu schema nouă)
def init_db():
    conn = _connect()
    cur = conn.cursor()

    # creează tabela dacă nu există deloc
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # MIGRARE: adaugă coloanele lipsă
    cols = {c[1] for c in cur.execute("PRAGMA table_info(users)").fetchall()}
    if "is_verified" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
    if "verify_token" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN verify_token TEXT")

    conn.commit()
    conn.close()


def create_user(email: str, password_hash: str, verify_token: str):
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (email, password, is_verified, verify_token) VALUES (?, ?, 0, ?)",
            (email, password_hash, verify_token),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Email already registered")
    finally:
        conn.close()

def get_user_by_email(email: str):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, password, is_verified, verify_token FROM users WHERE email = ?",
        (email,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "password": row[2],
        "is_verified": bool(row[3]),
        "verify_token": row[4],
    }

def get_user_by_token(token: str):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, password, is_verified, verify_token FROM users WHERE verify_token = ?",
        (token,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "password": row[2],
        "is_verified": bool(row[3]),
        "verify_token": row[4],
    }

def mark_verified(user_id: int):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_verified = 1, verify_token = NULL WHERE id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()

# creează tabela la import
init_db()
