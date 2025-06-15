import torch
import soundfile as sf
from config import SAMPLE_RATE, DEFAULT_SPEAKER

# Загружаем обе модели (русский и английский) один раз при импорте
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
print("Модели загружены.")

def get_lang_and_model(speaker):
    # Английские спикеры: en_0, en_1
    if speaker in ("en_0", "en_1"):
        return "en", en_model
    # Русские спикеры
    return "ru", ru_model

async def synthesize_speech(text, speaker, user_id):
    lang, model = get_lang_and_model(speaker or DEFAULT_SPEAKER.get("ru"))
    # По умолчанию если speaker не указан — используем дефолт для языка
    if not speaker:
        speaker = DEFAULT_SPEAKER.get(lang, "baya")
    audio = model.apply_tts(text, speaker=speaker, sample_rate=SAMPLE_RATE)
    temp_file = f"tts_{user_id}.wav"
    sf.write(temp_file, audio, SAMPLE_RATE)
    return temp_file