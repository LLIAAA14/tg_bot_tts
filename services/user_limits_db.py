import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = Path("user_limits.db")
FREE_LIMIT = 30
FLOOD_SECONDS = 5

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_limits (
                user_id TEXT PRIMARY KEY,
                used INTEGER NOT NULL DEFAULT 0,
                purchased INTEGER NOT NULL DEFAULT 0,
                last_request TEXT
            )
        """)

def now_iso():
    return datetime.utcnow().isoformat()

def get_user_limit(user_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    cur = conn.execute(
        "SELECT used, purchased, last_request FROM user_limits WHERE user_id=?",
        (str(user_id),)
    )
    row = cur.fetchone()
    if row:
        result = {"used": row[0], "purchased": row[1], "last_request": row[2]}
    else:
        conn.execute(
            "INSERT INTO user_limits (user_id, used, purchased, last_request) VALUES (?, ?, 0, NULL)",
            (str(user_id), 0)
        )
        result = {"used": 0, "purchased": 0, "last_request": None}
    if close_conn:
        conn.commit()
        conn.close()
    return result

def get_left(user_id):
    limit = get_user_limit(user_id)
    total = FREE_LIMIT + limit["purchased"]
    left = total - limit["used"]
    return max(left, 0)

def can_speak(user_id):
    limit = get_user_limit(user_id)
    total = FREE_LIMIT + limit["purchased"]
    return limit["used"] < total

def add_used(user_id):
    with get_conn() as conn:
        get_user_limit(user_id, conn=conn)  # Ensure exists
        conn.execute(
            "UPDATE user_limits SET used = used + 1 WHERE user_id=?",
            (str(user_id),)
        )
        conn.commit()

def add_purchased(user_id, amount):
    with get_conn() as conn:
        get_user_limit(user_id, conn=conn)  # Ensure exists
        conn.execute(
            "UPDATE user_limits SET purchased = purchased + ? WHERE user_id=?",
            (amount, str(user_id))
        )
        conn.commit()

def get_last_request(user_id):
    limit = get_user_limit(user_id)
    return limit.get("last_request")

def set_last_request(user_id):
    with get_conn() as conn:
        get_user_limit(user_id, conn=conn)
        conn.execute(
            "UPDATE user_limits SET last_request=? WHERE user_id=?",
            (now_iso(), str(user_id))
        )
        conn.commit()

def can_request(user_id):
    last = get_last_request(user_id)
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        delta = datetime.utcnow() - last_dt
        return delta.total_seconds() >= FLOOD_SECONDS
    except Exception:
        return True

def seconds_to_wait(user_id):
    last = get_last_request(user_id)
    if not last:
        return 0
    try:
        last_dt = datetime.fromisoformat(last)
        delta = datetime.utcnow() - last_dt
        left = FLOOD_SECONDS - delta.total_seconds()
        return max(int(left), 0)
    except Exception:
        return 0