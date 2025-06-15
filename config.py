from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
SAMPLE_RATE = 48000

# Расширенная структура SPEAKERS для поддержки языков
SPEAKERS = {
    "ru": ["aidar", "baya", "kseniya", "xenia", "eugene", "random"],
    "en": ["en_0", "en_1"]  # Silero TTS: en_0 - female, en_1 - male
}

DEFAULT_SPEAKER = {
    "ru": "baya",
    "en": "en_0"
}