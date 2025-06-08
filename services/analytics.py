import json
from pathlib import Path

STATS_FILE = Path("stats.json")

def load_stats():
    if STATS_FILE.exists():
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "total_users": 0,
        "total_tts": 0,
        "total_purchases": 0,
        "total_voices_purchased": 0,
        "users": {}
    }

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def register_user(user_id):
    stats = load_stats()
    s_id = str(user_id)
    if s_id not in stats["users"]:
        stats["users"][s_id] = {
            "tts_count": 0,
            "voices_purchased": 0
        }
        stats["total_users"] = len(stats["users"])
        save_stats(stats)

def increment_tts(user_id):
    register_user(user_id)          # Сначала регистрируем пользователя (если нет)
    stats = load_stats()            # Только теперь загружаем stats
    s_id = str(user_id)
    stats["total_tts"] += 1
    stats["users"][s_id]["tts_count"] += 1
    save_stats(stats)

def increment_purchase(user_id, amount):
    register_user(user_id)
    stats = load_stats()
    s_id = str(user_id)
    stats["total_purchases"] += 1
    stats["total_voices_purchased"] += amount
    stats["users"][s_id]["voices_purchased"] += amount
    save_stats(stats)

def get_stats():
    return load_stats()