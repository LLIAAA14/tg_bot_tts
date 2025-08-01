from pydub import AudioSegment

def convert_audio_format(input_path, output_path, target_format):
    """
    Конвертирует аудиофайл из WAV в target_format (mp3 или ogg).

    :param input_path: путь к исходному wav-файлу
    :param output_path: путь, куда сохранить сконвертированный файл
    :param target_format: 'mp3' или 'ogg'
    """
    # pydub поддерживает WAV/MP3/OGG, ffmpeg должен быть установлен в системе
    if target_format.lower() not in {"mp3", "ogg"}:
        raise ValueError("Поддерживаются только форматы mp3 и ogg")

    audio = AudioSegment.from_wav(input_path)
    audio.export(output_path, format=target_format.lower())