"""
This is where translation happens
input: text, language (optional)
output: translated text
"""
from googletrans import Translator
import json.decoder
from proxies import PROXIES

COUNTRIES = {'au': 'Australia',
             'ar':'Argentina',
             'am': 'Armenia',
             'by': 'Belarus',
             'bg': 'Bulgary',
             'br': 'Brazil',
             'gb': 'Great Britain',
             'ge': 'Georgia',
             'de': 'Germany',
             'gr': 'Greece',
             'hi': 'India',
             'it': 'Italy',
             'kz': 'Kazakhstan',
             'ca': 'Canada',
             'mx': 'Mexica',
             'nl': 'Netherlands',
             'pt': 'Portugal',
             'ru': 'Russia',
             'ro': 'Romania',
             'us': 'USA',
             'uz': 'Uzbekistan',
             'sg': 'Singapore',
             'tr': 'Turkey',
             'ua': 'Ukraine',
             'fi': 'Finland',
             'fr': 'France',
             'cz': 'Czech Republic',
             'ch': 'Switzerland',
             'ee': 'Estonia',
             'jp': 'Japan'}

COUNTRIES_R = {y: x for x,y in COUNTRIES.items()}

ENGLISH_SPEAKING = {'au': 'Australia',
                    'gb': 'Great Britain',
                    'us': 'USA',}


def translate(text, arg=None):
    try:
        t = Translator(proxies=PROXIES)

        try:
            if arg in COUNTRIES_R.keys():
                language = COUNTRIES_R[arg]
                translated_text = t.translate(text, dest=language).text
                # print(translated_text)
                return translated_text

            elif arg in COUNTRIES.keys():
                language = arg
                translated_text = t.translate(text, dest=language).text
                # print(translated_text)
                return translated_text
        except ValueError:
            translated_text = t.translate(text).text
            # print(translated_text)
            return translated_text

        return t.translate(text).text
    except json.decoder.JSONDecodeError:
        # print("Error")
        return ""


