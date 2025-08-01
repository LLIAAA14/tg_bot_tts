import torch
import soundfile as sf
import os
from config import SAMPLE_RATE, DEFAULT_SPEAKER, SPEAKERS
from services.tts_queue import tts_queue
from utils.audio_utils import convert_audio_format

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

def synthesize_text_to_audio(text, speaker, output_wav_path):
    lang, model = get_lang_and_model(speaker)
    audio = model.apply_tts(
        text=text,
        speaker=speaker,
        sample_rate=SAMPLE_RATE
    )
    sf.write(output_wav_path, audio, SAMPLE_RATE)
    return output_wav_path

async def queue_tts_synthesis(text, speaker, user_id=None, notify_func=None, audio_format="wav"):
    """
    text: текст для синтеза
    speaker: имя диктора
    user_id: id пользователя (для очереди, не для имени файла)
    notify_func: функция для уведомлений
    audio_format: "wav", "mp3" или "ogg"
    """
    async def job():
        base_name = f"output_{speaker}_{user_id if user_id is not None else 'user'}.wav"
        wav_path = synthesize_text_to_audio(text, speaker, base_name)

        if audio_format == "wav":
            return wav_path

        # Конвертация в нужный формат
        ext = audio_format.lower()
        out_path = base_name.replace(".wav", f".{ext}")
        convert_audio_format(wav_path, out_path, ext)

        # Удаляем временный wav файл, если нужен только другой формат
        try:
            os.remove(wav_path)
        except Exception:
            pass

        return out_path

    return await tts_queue.run(job, user_id=user_id, notify_func=notify_func)