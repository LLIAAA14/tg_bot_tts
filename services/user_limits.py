import json
from pathlib import Path
from datetime import datetime, timedelta

LIMITS_FILE = Path("user_limits.json")
FREE_LIMIT = 30
FLOOD_SECONDS = 5

def load_limits():
    if LIMITS_FILE.exists():
        with open(LIMITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_limits(data):
    with open(LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def now_iso():
    return datetime.utcnow().isoformat()

def get_user_limit(user_id):
    user_limits = load_limits()
    s_id = str(user_id)
    u = user_limits.get(s_id)
    if not u:
        user_limits[s_id] = {
            "used": 0,
            "purchased": 0,
            "last_request": None
        }
        save_limits(user_limits)
        return user_limits[s_id]
    if "last_request" not in u:
        u["last_request"] = None
        user_limits[s_id] = u
        save_limits(user_limits)
    return user_limits[s_id]

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
    user_limits = load_limits()
    s_id = str(user_id)
    limit = user_limits.get(s_id)
    if not limit:
        limit = get_user_limit(user_id)
    limit["used"] += 1
    user_limits[s_id] = limit
    save_limits(user_limits)

def add_purchased(user_id, amount):
    user_limits = load_limits()
    s_id = str(user_id)
    limit = user_limits.get(s_id)
    if not limit:
        limit = get_user_limit(user_id)
    limit["purchased"] += amount
    user_limits[s_id] = limit
    save_limits(user_limits)

# АНТИФЛУД
def get_last_request(user_id):
    limit = get_user_limit(user_id)
    return limit.get("last_request")

def set_last_request(user_id):
    user_limits = load_limits()
    s_id = str(user_id)
    limit = user_limits.get(s_id)
    if not limit:
        limit = get_user_limit(user_id)
    limit["last_request"] = datetime.utcnow().isoformat()
    user_limits[s_id] = limit
    save_limits(user_limits)

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