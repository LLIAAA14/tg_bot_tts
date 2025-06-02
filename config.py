from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
SAMPLE_RATE = 48000
SPEAKERS = ["aidar", "baya", "kseniya", "xenia", "eugene", "random"]
DEFAULT_SPEAKER = "baya"