import torch
import soundfile as sf
from config import SAMPLE_RATE, DEFAULT_SPEAKER, SPEAKERS
from services.tts_queue import tts_queue

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

def synthesize_text_to_audio(text, speaker):
    lang, model = get_lang_and_model(speaker)
    audio = model.apply_tts(
        text=text,
        speaker=speaker,
        sample_rate=SAMPLE_RATE
    )
    file_path = f"output_{speaker}.wav"
    sf.write(file_path, audio, SAMPLE_RATE)
    return file_path

async def queue_tts_synthesis(text, speaker, user_id=None, notify_func=None):
    async def job():
        return synthesize_text_to_audio(text, speaker)

    return await tts_queue.run(job, user_id=user_id, notify_func=notify_func)