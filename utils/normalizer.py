from num2words import num2words
import re

LANG_MAP = {
    "ru": "ru",
    "en": "en",
    "de": "de",
    "fr": "fr",
    "es": "es",
}

def normalize_numbers(text, lang='ru'):
    """
    Заменяет целые числа на текстовые эквиваленты.
    lang: 'ru', 'en', 'de', 'fr', 'es',
    """
    def repl(match):
        num = int(match.group(0))
        try:
            nlang = LANG_MAP.get(lang, "ru")
            return num2words(num, lang=nlang)
        except Exception:
            return match.group(0)
    return re.sub(r'\d+', repl, text)