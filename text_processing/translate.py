"""
This is where translation happens
input: text, language (optional)
output: translated text
"""
from googletrans import Translator
import json.decoder
# from proxies import PROXIES
from bs4 import BeautifulSoup
import requests

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

COUNTRIES_R = {y: x for x, y in COUNTRIES.items()}

ENGLISH_SPEAKING = {'au': 'Australia',
                    'gb': 'Great Britain',
                    'us': 'USA'}

FIRST_RUN = True


def get_proxies():
    proxies = {}
    page = requests.get('https://free-proxy-list.net')
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find(id='proxylisttable')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        proxy_host = 'https://'+cols[0]
        proxy_port = ':'+cols[1]
        proxies[proxy_host] = proxy_port
    proxies_list = [key+' '+value for key, value in proxies.items()]
    proxies_string = '\n'.join(proxies_list)

    if FIRST_RUN:
        with open('proxies.txt','w') as f:
            f.write(proxies_string)

    return proxies


def translate(text, country_or_language=None):
    try:
        global FIRST_RUN
        if FIRST_RUN:
            proxies = get_proxies()
        else:
            with open('proxies.txt','r') as f:
                proxies_string = f.read()
                proxies_list = proxies_string.split('\n')
                proxies = {key: value for proxy in proxies_list for key, value in proxy.split()}

        t = Translator(proxies=proxies)

        try:
            if country_or_language in COUNTRIES_R.keys():
                language = COUNTRIES_R[country_or_language]
                translated_text = t.translate(text, dest=language).text
                FIRST_RUN = False

                return translated_text

            elif country_or_language in COUNTRIES.keys():
                language = country_or_language
                translated_text = t.translate(text, dest=language).text
                FIRST_RUN = False

                return translated_text
        except ValueError:

            translated_text = t.translate(text).text
            FIRST_RUN = False
            return translated_text

        FIRST_RUN = False
        return t.translate(text).text

    except json.decoder.JSONDecodeError:
        FIRST_RUN = False
        return ""


print(translate('Белая мышь'))