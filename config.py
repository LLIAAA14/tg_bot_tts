from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
SAMPLE_RATE = 48000

# Только реально поддерживаемые языки и спикеры Silero TTS (2024)
SPEAKERS = {
    "ru": ['aidar', 'baya', 'kseniya', 'xenia', 'eugene'],
    "en": ['en_0', 'en_1', 'en_2', 'en_3', 'en_4'],
    "de": ['bernd_ungerer', 'eva_k', 'friedrich', 'hokuspokus', 'karlsson'],
    "fr": ['fr_0', 'fr_1', 'fr_2', 'fr_3', 'fr_4', 'fr_5'],
    "es": ['es_0', 'es_1', 'es_2'],
}

DEFAULT_SPEAKER = {
    "ru": "baya",
    "en": "en_0",
    "de": "bernd_ungerer",
    "fr": "fr_0",
    "es": "es_0",
}
