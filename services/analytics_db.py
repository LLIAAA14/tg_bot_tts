import sqlite3
from pathlib import Path

DB_FILE = Path("stats.db")

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_conn() as conn:
        # Храним глобальные счетчики и пользователей
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                tts_count INTEGER NOT NULL DEFAULT 0,
                voices_purchased INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Заполнить глобальные счетчики если пусто
        for key in ("total_users", "total_tts", "total_purchases", "total_voices_purchased"):
            cur = conn.execute("SELECT value FROM stats WHERE key=?", (key,))
            if cur.fetchone() is None:
                conn.execute("INSERT INTO stats (key, value) VALUES (?, 0)", (key,))

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

def register_user(user_id):
    s_id = str(user_id)
    with get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id=?", (s_id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO users (user_id, tts_count, voices_purchased) VALUES (?, 0, 0)",
                (s_id,)
            )
            conn.execute("UPDATE stats SET value = value + 1 WHERE key='total_users'")

def increment_tts(user_id):
    s_id = str(user_id)
    register_user(s_id)
    with get_conn() as conn:
        conn.execute("UPDATE stats SET value = value + 1 WHERE key='total_tts'")
        conn.execute("UPDATE users SET tts_count = tts_count + 1 WHERE user_id=?", (s_id,))

def increment_purchase(user_id, amount):
    s_id = str(user_id)
    register_user(s_id)
    with get_conn() as conn:
        conn.execute("UPDATE stats SET value = value + 1 WHERE key='total_purchases'")
        conn.execute("UPDATE stats SET value = value + ? WHERE key='total_voices_purchased'", (amount,))
        conn.execute("UPDATE users SET voices_purchased = voices_purchased + ? WHERE user_id=?", (amount, s_id))

def get_stats():
    with get_conn() as conn:
        stats = {
            "total_users": get_stat("total_users"),
            "total_tts": get_stat("total_tts"),
            "total_purchases": get_stat("total_purchases"),
            "total_voices_purchased": get_stat("total_voices_purchased"),
            "users": {}
        }
        cur = conn.execute("SELECT user_id, tts_count, voices_purchased FROM users")
        for row in cur.fetchall():
            stats["users"][row[0]] = {
                "tts_count": row[1],
                "voices_purchased": row[2]
            }
        return stats