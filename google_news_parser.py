from newsapi import NewsApiClient
import sqlite3
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
                                      language='en',
                                      sort_by='relevancy',
                                      page=2)

# /v2/sources
sources = newsapi.get_sources()
"""

API_KEY = 'c0cd81357fb64023bcdcaaea3faedd3c'

# Init
newsapi = NewsApiClient(api_key=API_KEY)


query = input("Enter search query: ")
countries = input("Enter countries: ")


for c in countries.split(', '):
    all_articles = newsapi.get_top_headlines(q=query,
                                             country=c,
                                             page_size=50)

    for a in all_articles['articles']:
            date = a["publishedAt"].split('T')[0]

            create_news_item(country=c,
                             reference=a['url'],
                             date=date,
                             title=a['title'],
                             lead=a['description'],
                             content=a['content'])