from num2words import num2words
import re

def normalize_numbers(text, lang='ru'):
    """
    Заменяет целые числа на текстовые эквиваленты.
    lang: 'ru' для русского, 'en' для английского.
    """
    def repl(match):
        num = int(match.group(0))
        try:
            return num2words(num, lang=lang)
        except Exception:
            return match.group(0)
    return re.sub(r'\d+', repl, text)