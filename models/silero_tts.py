import torch
import soundfile as sf
from config import SAMPLE_RATE, DEFAULT_SPEAKER, SPEAKERS

print("Загрузка Silero TTS моделей...")

ru_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v3_1_ru'
)
en_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='en',
    speaker='v3_en'
)
de_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='de',
    speaker='v3_de'
)
fr_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='fr',
    speaker='v3_fr'
)
es_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='es',
    speaker='v3_es'
)

print("Модели загружены.")

def get_lang_and_model(speaker):
    if speaker in SPEAKERS["en"]:
        return "en", en_model
    if speaker in SPEAKERS["de"]:
        return "de", de_model
    if speaker in SPEAKERS["fr"]:
        return "fr", fr_model
    if speaker in SPEAKERS["es"]:
        return "es", es_model
    return "ru", ru_model

async def synthesize_speech(text, speaker, user_id):
    lang, model = get_lang_and_model(speaker or DEFAULT_SPEAKER.get("ru"))
    if not speaker:
        speaker = DEFAULT_SPEAKER.get(lang, "baya")
    audio = model.apply_tts(text, speaker=speaker, sample_rate=SAMPLE_RATE)
    temp_file = f"tts_{user_id}.wav"
    sf.write(temp_file, audio, SAMPLE_RATE)
    return temp_file