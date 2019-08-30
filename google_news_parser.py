from newsapi import NewsApiClient
from db_management import create_news_item

""" 
Example API:

# /v2/top-headlines
top_headlines = newsapi.get_top_headlines(q='bitcoin',
                                          category='business',
                                          language='en',
                                          country='us')

# /v2/everything
all_articles = newsapi.get_everything(q='bitcoin',
                                      sources='bbc-news,the-verge',
                                      domains='bbc.co.uk,techcrunch.com',
                                      from_param='2019-08-20',
                                      to='2019-08-23',
                                      language='en',
                                      sort_by='relevancy',
                                      page=2)

# /v2/sources
sources = newsapi.get_sources()
"""
API_KEY = 'c0cd81357fb64023bcdcaaea3faedd3c'
# Init
newsapi = NewsApiClient(api_key=API_KEY)


def get_news_everything(query, languages, date_from, date_to):

        all_articles = []

        for l in languages:
            articles = newsapi.get_everything(q=query,
                                              language=l,
                                              page_size=50,
                                              from_param=str(date_from),
                                              to=str(date_to),
                                              sort_by='popularity')

            all_articles.extend(articles['articles'])

            for a in all_articles:
                    date = a["publishedAt"].split('T')[0]

                    create_news_item(country=l,
                                     reference=a['url'],
                                     date=date,
                                     title=a['title'],
                                     lead=a['description'],
                                     content=a['content'])

        return all_articles


def get_news_top(query, countries):
    all_articles = []

    for c in countries:
        articles = newsapi.get_top_headlines(q=query,
                                             country=c)

        all_articles.extend(articles['articles'])

        for a in all_articles:
            date = a["publishedAt"].split('T')[0]

            create_news_item(country=c,
                             reference=a['url'],
                             date=date,
                             title=a['title'],
                             lead=a['description'],
                             content=a['content'])

    return all_articles


typ = input("Query type (top/everything): ")
query = input("Query: ")
if typ == 'everything':
    date_from = input("Date from (YYYY-MM-DD): ")
    date_to = input("Date to (YYYY-MM-DD): ")
    languages = input("Languages: ")
    get_news_everything(query, languages.split(', '), date_from, date_to)
elif typ == 'top':
    countries = input("Countries: ")
    get_news_top(query, countries.split(', '))
