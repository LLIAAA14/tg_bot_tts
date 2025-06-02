import torch
import soundfile as sf
from config import SAMPLE_RATE, DEFAULT_SPEAKER

# Загружаем модель один раз при импорте
print("Загрузка Silero TTS...")
model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v3_1_ru'
)
print("Модель загружена.")

async def synthesize_speech(text, speaker, user_id):
    # Генерация речи и сохранение файла
    audio = model.apply_tts(text, speaker=speaker or DEFAULT_SPEAKER, sample_rate=SAMPLE_RATE)
    temp_file = f"tts_{user_id}.wav"
    sf.write(temp_file, audio, SAMPLE_RATE)
    return temp_file