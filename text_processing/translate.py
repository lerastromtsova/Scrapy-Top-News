"""
This is where translation happens
input: text, language (optional)
output: translated text
"""

from bs4 import BeautifulSoup
import requests

COUNTRIES = {'au': 'Australia',
             'ar': 'Argentina',
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

TOKENS = {'trnsl.1.1.20190320T191119Z.7351437d92ff7331.6a7239f25a8ae9c0d0f1a4192301b9d447eab01d': True,
          'trnsl.1.1.20190324T122545Z.d2cefeb8436fa25d.466c8cb810cd05d3c91df5d9c43339ec0158af52': True,
          'trnsl.1.1.20190324T123819Z.ae1376d58c058e27.3ef28a8850873e392ff616696313a1aa78533672': True,
          'trnsl.1.1.20190324T123930Z.d76200e81a2da8ed.868ea98fbf2f0ed90dbb9ea39837ab58787232bb': True,
          'trnsl.1.1.20190324T124007Z.73f112ac6f237288.88be3b84cde618ab7f91db86faadd13d5f29a910': True,
          'trnsl.1.1.20190324T124128Z.4732083aac8129a2.876ae256ecce87521191a8453c6fa712bdaa22b2': True,
          'trnsl.1.1.20190324T124252Z.3fd1890c1675c3d8.4963dfaa02306856a24d4be7267aaebb7df5b168': True,
          'trnsl.1.1.20190324T124413Z.c3362db269d313f1.ff6ff7569e4e0e3dbc4177d3fcc00f4bbede9e7f': True,
          'trnsl.1.1.20190324T124529Z.4f092762d7b9901d.00157461cba04514df89fc7f2bfa11d854618839': True}

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
        proxy_host = 'https://' + cols[0]
        proxy_port = ':' + cols[1]
        proxies.append({proxy_host: proxy_port})
    proxies_list = [key + ' ' + value for proxy in proxies for key, value in proxy.items()]
    proxies_string = '\n'.join(proxies_list)

    if FIRST_RUN:
        with open('proxies.txt', 'w') as f:
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
        proxy_host = 'https://' + cols[0]
        proxy_port = ':' + cols[1]
        proxies[proxy_host] = proxy_port
    proxies_list = [key + ' ' + value for key, value in proxies.items()]
    proxies_string = '\n'.join(proxies_list)

    if FIRST_RUN:
        with open('proxies.txt', 'w') as f:
            f.write(proxies_string)

    return proxies


def translation_request(text, target_language):
    url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'

    for token, isalive in TOKENS.items():

        if isalive:

            data = {'key': token,
                    'lang': target_language,
                    'text': text}

            r = requests.get(url, params=data)
            result = r.json()

            try:
                return result['text'][0]
            except KeyError:
                TOKENS[token] = False

    raise Exception('There are no tokens left :(')


def translate(text, country_or_language=None):
    if country_or_language in COUNTRIES_R.keys():
        language = COUNTRIES_R[country_or_language]
    else:
        language = country_or_language

    try:
        return translation_request(text, language)
    except requests.exceptions.ConnectionError:
        return translate(text, language)


