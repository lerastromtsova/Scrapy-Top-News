from newsapi import NewsApiClient
from datetime import datetime
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

query = input()
date_from = input()

all_articles = newsapi.get_everything(q=query,
                                      from_param=date_from,
                                      language='en',
                                      sort_by='relevancy')

total_results = all_articles['totalResults']

for i in range(20, total_results, 20):
    all_articles = newsapi.get_everything(q=query,
                                          from_param=date_from,
                                          language='en',
                                          sort_by='relevancy',
                                          page=i//20)
    for a in all_articles['articles']:
        print(a['title'])


