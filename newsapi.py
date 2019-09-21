from contextlib import contextmanager
from collections import OrderedDict
from language_choices import short_codes as language_choices
from country_choices import short_codes as country_choices

import config
import pytest
import requests

""" 
Example API:

# /v2/top-headlines
top_headlines = top_headlines(q='bitcoin',
                              category='business',
                              language='en',
                              country='us')

# /v2/everything
all_articles = everything(q='bitcoin',
                          sources='bbc-news,the-verge',
                          domains='bbc.co.uk,techcrunch.com',
                          from_param='2019-08-20',
                          to='2019-08-23',
                          language='en',
                          sort_by='relevancy',
                          page=2)
"""


@contextmanager
def does_not_raise():
    yield


@pytest.mark.parametrize(
    'test_params, test_rc',
    [({'country': 'us', 'q': 'trump'}, 'ok')]
)
def test_top_headlines(test_params, test_rc):
    assert top_headlines(**test_params)['status'] == test_rc


@pytest.mark.parametrize(
    'test_params, test_rc',
    [({'language': 'en', 'q': 'trump'}, 'ok')]
)
def test_everything(test_params, test_rc):
    assert everything(**test_params)['status'] == test_rc


@pytest.mark.parametrize(
    'test_params, expected_exception',
    [(dict(mode='top', q='trump', countries=['us', 'ru']), does_not_raise()),
     (dict(mode='everything', q='trump', date_from='2019-09-01', date_to='2019-09-23', languages=['en', 'ru']),
      does_not_raise()),
     (dict(mode='test_mode'), pytest.raises(Exception))]
)
def test_get_news(test_params, expected_exception):
    with expected_exception:
        articles = get_news(**test_params)
        assert isinstance(articles, dict)
        assert set(articles.keys()).issubset(language_choices) or set(articles.keys()).issubset(country_choices)


def top_headlines(**kwargs):
    response = requests.get(
        url='https://newsapi.org/v2/top-headlines',
        params=kwargs,
        headers={'X-Api-Key': config.GOOGLE_API_KEY}
    )
    return response.json()


def everything(**kwargs):
    response = requests.get(
        url='https://newsapi.org/v2/everything',
        params=kwargs,
        headers={'X-Api-Key': config.GOOGLE_API_KEY}
    )
    return response.json()


def get_news(**kwargs):
    articles = dict()

    params = kwargs
    mode = kwargs['mode']
    parameters = OrderedDict({
        'top': {
            'kw_plural': 'countries',
            'kw_singular': 'country',
            'target_function': top_headlines
        },
        'everything': {
            'kw_plural': 'languages',
            'kw_singular': 'language',
            'target_function': everything
        }
    })

    kw_plural = kwargs[parameters[mode]['kw_plural']]
    for kw in kw_plural:
        params[parameters[mode]['kw_singular']] = kw
        articles[kw] = parameters[mode]['target_function'](**params)['articles']
    return articles
