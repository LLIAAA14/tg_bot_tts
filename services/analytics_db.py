import sqlite3
from pathlib import Path

DB_FILE = Path("stats.db")

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_conn() as conn:
        # Глобальные счетчики и пользователи (расширенные)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                stt_count INTEGER NOT NULL DEFAULT 0,
                recognitions_purchased INTEGER NOT NULL DEFAULT 0,
                registered_at TEXT,
                last_active TEXT,
                source TEXT
            )
        """)
        # Журнал событий
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user_time ON events (user_id, timestamp)")
        # Журнал ошибок
        conn.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                error_type TEXT,
                error_message TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_errors_user_time ON errors (user_id, timestamp)")
        # Заполнить глобальные счетчики если пусто
        for key in ("total_users", "total_stt", "total_purchases", "total_recognitions_purchased"):
            cur = conn.execute("SELECT value FROM stats WHERE key=?", (key,))
            if cur.fetchone() is None:
                conn.execute("INSERT INTO stats (key, value) VALUES (?, 0)", (key,))

def log_event(user_id, action, details=None):
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO events (user_id, action, timestamp, details) VALUES (?, ?, ?, ?)",
            (str(user_id), action, now, details)
        )
        conn.commit()

def log_error(user_id, error_type, error_message):
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO errors (user_id, error_type, error_message, timestamp) VALUES (?, ?, ?, ?)",
            (str(user_id), error_type, error_message, now)
        )
        conn.commit()

def get_stat(key):
    with get_conn() as conn:
        cur = conn.execute("SELECT value FROM stats WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else 0

def set_stat(key, value):
    with get_conn() as conn:
        conn.execute("UPDATE stats SET value=? WHERE key=?", (value, key))

def inc_stat(key, amount=1):
    with get_conn() as conn:
        conn.execute("UPDATE stats SET value = value + ? WHERE key=?", (amount, key))

def register_user(user_id, source=None):
    from datetime import datetime
    s_id = str(user_id)
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id=?", (s_id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO users (user_id, stt_count, recognitions_purchased, registered_at, last_active, source) VALUES (?, 0, 0, ?, ?, ?)",
                (s_id, now, now, source)
            )
            conn.execute("UPDATE stats SET value = value + 1 WHERE key='total_users'")

def update_last_active(user_id):
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_active=? WHERE user_id=?", (now, str(user_id)))

def increment_tts(user_id):
    increment_stt(user_id)

def increment_stt(user_id):
    from datetime import datetime
    s_id = str(user_id)
    register_user(s_id)
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE stats SET value = value + 1 WHERE key='total_stt'")
        conn.execute("UPDATE users SET stt_count = stt_count + 1, last_active=? WHERE user_id=?", (now, s_id))
        conn.execute(
            "INSERT INTO events (user_id, action, timestamp, details) VALUES (?, ?, ?, ?)",
            (s_id, "stt", now, None)
        )

def increment_purchase(user_id, amount, details=None):
    from datetime import datetime
    s_id = str(user_id)
    register_user(s_id)
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE stats SET value = value + 1 WHERE key='total_purchases'")
        conn.execute("UPDATE stats SET value = value + ? WHERE key='total_recognitions_purchased'", (amount,))
        conn.execute("UPDATE users SET recognitions_purchased = recognitions_purchased + ?, last_active=? WHERE user_id=?", (amount, now, s_id))
        conn.execute(
            "INSERT INTO events (user_id, action, timestamp, details) VALUES (?, ?, ?, ?)",
            (s_id, "purchase", now, details)
        )

def get_stats():
    with get_conn() as conn:
        stats = {
            "total_users": get_stat("total_users"),
            "total_stt": get_stat("total_stt"),
            "total_purchases": get_stat("total_purchases"),
            "total_recognitions_purchased": get_stat("total_recognitions_purchased"),
            "users": {}
        }
        cur = conn.execute("SELECT user_id, stt_count, recognitions_purchased, registered_at, last_active, source FROM users")
        for row in cur.fetchall():
            stats["users"][row[0]] = {
                "stt_count": row[1],
                "recognitions_purchased": row[2],
                "registered_at": row[3],
                "last_active": row[4],
                "source": row[5]
            }
        return stats

def get_events(user_id=None, action=None, since=None, limit=100):
    query = "SELECT user_id, action, timestamp, details FROM events WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id=?"
        params.append(str(user_id))
    if action:
        query += " AND action=?"
        params.append(action)
    if since:
        query += " AND timestamp>=?"
        params.append(since)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        cur = conn.execute(query, tuple(params))
        return cur.fetchall()

def get_errors(user_id=None, since=None, limit=100):
    query = "SELECT user_id, error_type, error_message, timestamp FROM errors WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id=?"
        params.append(str(user_id))
    if since:
        query += " AND timestamp>=?"
        params.append(since)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        cur = conn.execute(query, tuple(params))
        return cur.fetchall()