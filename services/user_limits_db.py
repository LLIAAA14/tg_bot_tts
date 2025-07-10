import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = Path("user_limits.db")
FREE_LIMIT = 30  # 30 бесплатных озвучек
FLOOD_SECONDS = 5

def get_conn():
    return sqlite3.connect(DB_FILE)

def now_iso():
    return datetime.utcnow().isoformat()

def init_db():
    with get_conn() as conn:
        # Основная таблица лимитов пользователей
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS user_limits (
                user_id TEXT PRIMARY KEY,
                used INTEGER NOT NULL DEFAULT 0,
                purchased INTEGER NOT NULL DEFAULT 0,
                cumulative INTEGER NOT NULL DEFAULT 0,
                last_request TEXT,
                last_used TEXT,
                registered_at TEXT,
                free_limit INTEGER NOT NULL DEFAULT {FREE_LIMIT},
                frozen INTEGER NOT NULL DEFAULT 0
            )
        """)
        # История пополнений и использования
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_limit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL, -- 'purchase', 'use', 'limit_exceeded'
                amount INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                comment TEXT
            )
        """)
        # Индекс для быстрого поиска по user_id и времени
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_user_time ON user_limit_history (user_id, timestamp)")

def ensure_user(user_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    cur = conn.execute("SELECT 1 FROM user_limits WHERE user_id=?", (str(user_id),))
    if not cur.fetchone():
        now = now_iso()
        conn.execute(
            "INSERT INTO user_limits (user_id, used, purchased, cumulative, last_request, last_used, registered_at, free_limit, frozen) VALUES (?, 0, 0, 0, NULL, NULL, ?, ?, 0)",
            (str(user_id), now, FREE_LIMIT)
        )
    if close_conn:
        conn.commit()
        conn.close()

def get_user_limit(user_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    cur = conn.execute(
        """SELECT used, purchased, cumulative, last_request, last_used, registered_at, free_limit, frozen
           FROM user_limits WHERE user_id=?""",
        (str(user_id),)
    )
    row = cur.fetchone()
    if row:
        keys = ("used", "purchased", "cumulative", "last_request", "last_used", "registered_at", "free_limit", "frozen")
        result = dict(zip(keys, row))
    else:
        ensure_user(user_id, conn)
        result = {
            "used": 0,
            "purchased": 0,
            "cumulative": 0,
            "last_request": None,
            "last_used": None,
            "registered_at": now_iso(),
            "free_limit": FREE_LIMIT,
            "frozen": 0
        }
    if close_conn:
        conn.commit()
        conn.close()
    return result

def get_left(user_id):
    limit = get_user_limit(user_id)
    total = limit["free_limit"] + limit["purchased"]
    left = total - limit["used"]
    return max(left, 0)

def can_speak(user_id, required=1):
    limit = get_user_limit(user_id)
    if limit["frozen"]:
        return False
    total = limit["free_limit"] + limit["purchased"]
    return (limit["used"] + required) <= total

def add_used(user_id, amount=1, comment=None):
    now = now_iso()
    with get_conn() as conn:
        ensure_user(user_id, conn=conn)
        conn.execute(
            "UPDATE user_limits SET used = used + ?, cumulative = cumulative + ?, last_used=? WHERE user_id=?",
            (int(amount), int(amount), now, str(user_id))
        )
        conn.execute(
            "INSERT INTO user_limit_history (user_id, action, amount, timestamp, comment) VALUES (?, 'use', ?, ?, ?)",
            (str(user_id), int(amount), now, comment)
        )
        conn.commit()

def add_purchased(user_id, amount, comment=None):
    now = now_iso()
    with get_conn() as conn:
        ensure_user(user_id, conn=conn)
        conn.execute(
            "UPDATE user_limits SET purchased = purchased + ? WHERE user_id=?",
            (int(amount), str(user_id))
        )
        conn.execute(
            "INSERT INTO user_limit_history (user_id, action, amount, timestamp, comment) VALUES (?, 'purchase', ?, ?, ?)",
            (str(user_id), int(amount), now, comment)
        )
        conn.commit()

def set_last_request(user_id):
    now = now_iso()
    with get_conn() as conn:
        ensure_user(user_id, conn=conn)
        conn.execute(
            "UPDATE user_limits SET last_request=? WHERE user_id=?",
            (now, str(user_id))
        )
        conn.commit()

def set_frozen(user_id, state=True):
    with get_conn() as conn:
        ensure_user(user_id, conn=conn)
        conn.execute(
            "UPDATE user_limits SET frozen=? WHERE user_id=?",
            (1 if state else 0, str(user_id))
        )
        conn.commit()

def set_free_limit(user_id, free_amount):
    with get_conn() as conn:
        ensure_user(user_id, conn=conn)
        conn.execute(
            "UPDATE user_limits SET free_limit=? WHERE user_id=?",
            (int(free_amount), str(user_id))
        )
        conn.commit()

def log_limit_exceeded(user_id, required=1, comment=None):
    now = now_iso()
    with get_conn() as conn:
        ensure_user(user_id, conn=conn)
        conn.execute(
            "INSERT INTO user_limit_history (user_id, action, amount, timestamp, comment) VALUES (?, 'limit_exceeded', ?, ?, ?)",
            (str(user_id), int(required), now, comment)
        )
        conn.commit()

def get_history(user_id, limit=20):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT action, amount, timestamp, comment FROM user_limit_history WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
            (str(user_id), limit)
        )
        return cur.fetchall()

def get_last_request(user_id):
    limit = get_user_limit(user_id)
    return limit.get("last_request")

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

def pretty_count(amount: int):
    return f"{amount} озвучек"