from num2words import num2words
import re

def normalize_numbers(text):
    # Заменяет целые числа на текстовые эквиваленты (на русском)
    def repl(match):
        num = int(match.group(0))
        try:
            return num2words(num, lang='ru')
        except Exception:
            return match.group(0)
    return re.sub(r'\d+', repl, text)