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
                    'en': 'England',
                    'us': 'USA'}

FIRST_RUN = True
I = 0


def get_proxies_list():
    proxies = []
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
        proxies.append({proxy_host: proxy_port})
    proxies_list = [key+' '+value for proxy in proxies for key, value in proxy.items() ]
    proxies_string = '\n'.join(proxies_list)

    if FIRST_RUN:
        with open('proxies.txt','w') as f:
            f.write(proxies_string)

    return proxies


def get_proxies_dict():
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
    proxies_list = [key+' '+value for key, value in proxies.items() ]
    proxies_string = '\n'.join(proxies_list)

    if FIRST_RUN:
        with open('proxies.txt','w') as f:
            f.write(proxies_string)

    return proxies


def translation_request(text, target_language):

    url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    token = 'trnsl.1.1.20190320T191119Z.7351437d92ff7331.6a7239f25a8ae9c0d0f1a4192301b9d447eab01d'
    data = {'key': token,
            'lang': target_language,
            'text': text}

    r = requests.get(url, params=data)
    return r.json()


def translate(text, country_or_language=None):
    if country_or_language in COUNTRIES_R.keys():
        language = COUNTRIES_R[country_or_language]
    else:
        language = country_or_language
    return translation_request(text, language)['text'][0]


def translate_old(text, country_or_language=None):
    global FIRST_RUN
    global I

    try:
        if FIRST_RUN:
            proxies = get_proxies_list()
        else:
            with open('proxies.txt','r') as f:
                proxies_string = f.read()
                proxies_list = proxies_string.split('\n')
                proxies_list = [proxy.split() for proxy in proxies_list]
                proxies = [{key: value} for key, value in proxies_list]


        try:
            t = Translator(proxies=dict(proxies[I]))
            I+= 1

        except IndexError:
            I = 0
            t = Translator(proxies=dict(proxies[I]))

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
        FIRST_RUN = True
        print(country_or_language)
        print(I)
        print("Could not translate text ", text[0:20])
        return translate(text, country_or_language)


translation_request('day', 'fr')
