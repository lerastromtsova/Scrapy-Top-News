def translation_request(text, target_language):

    url = 'https://translate.google.com'
    data = {'op': 'translate',
            'tl': target_language,
            'text': text}

    if FIRST_RUN:
        proxies = get_proxies()
    else:
        with open('proxies.txt', 'r') as f:
            proxies_string = f.read()
            proxies_list = proxies_string.split('\n')
            proxies_list = [proxy.split() for proxy in proxies_list]
            proxies = [{key: value} for key, value in proxies_list]

    r = requests.get(url, params=data, proxies=proxies)
    print(r.text)