"""
This is where translation happens
input: text, language (optional)
output: translated text
"""
from googletrans import Translator
import json.decoder

def translate(text, language=None):
    t = Translator()
    try:
        if language:
            return t.translate(text, language).text
        else:
            return t.translate(text).text
    except json.decoder.JSONDecodeError as err:
        pass