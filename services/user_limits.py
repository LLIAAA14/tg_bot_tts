import json
from pathlib import Path

LIMITS_FILE = Path("user_limits.json")
FREE_LIMIT = 20

def load_limits():
    if LIMITS_FILE.exists():
        with open(LIMITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_limits(data):
    with open(LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

user_limits = load_limits()

def get_user_limit(user_id):
    return user_limits.get(str(user_id), {"used": 0, "purchased": 0})

def can_speak(user_id):
    limit = get_user_limit(user_id)
    total = FREE_LIMIT + limit["purchased"]
    return limit["used"] < total

def add_used(user_id):
    limit = get_user_limit(user_id)
    limit["used"] += 1
    user_limits[str(user_id)] = limit
    save_limits(user_limits)

def add_purchased(user_id, amount):
    limit = get_user_limit(user_id)
    limit["purchased"] += amount
    user_limits[str(user_id)] = limit
    save_limits(user_limits)

def get_left(user_id):
    limit = get_user_limit(user_id)
    total = FREE_LIMIT + limit["purchased"]
    left = total - limit["used"]
    return max(left, 0)