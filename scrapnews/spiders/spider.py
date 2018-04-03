import scrapy
from scrapnews.items import NewsItem
from scrapnews.translate import translate
from scrapnews.preprocess import preprocess
from datetime import date
import sqlite3
import os

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
             'in': 'India',
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

COUNTRIES_R = {y:x for x,y in COUNTRIES.items()}

PERIODS = {'online','hour','day','week','month'}

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..','db','topnews.db')


class NewsSpider(scrapy.Spider):
    name = "news"

    def __init__(self, countries, period, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        if countries=="All":
            self.start_urls = ['https://top.st/' + co + "/" + period for co in COUNTRIES.keys()]
        else:
            self.start_urls = ['https://top.st/' + country + "/" + period for country in countries]

    def parse(self, response):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for i,new in enumerate(response.css('h2')):

            item = NewsItem()
            url = new.css('a::attr(href)').extract_first()
            title = new.css('a::text').extract_first()
            co = response.url.split('/')[-2]
            c.execute("SELECT * FROM topnews WHERE url=?",(url,))
            res = c.fetchone()

            if res:
                item['url'] = res[1]
                item['title'] = res[2]
                item['number'] = res[3]
                item['country'] = res[4]
                item['tokens'] = res[5]
                item['scraping_date'] = str(date.today())
                item['scraping_type'] = response.url.split('/')[-1]

                yield item

            else:

                if co not in ('gb','us'):
                    title = translate(title)
                item['url'] = url
                item['title'] = title
                item['number'] = i + 1
                item['country'] = COUNTRIES[co]
                item['tokens'] = preprocess(title)
                item['scraping_date'] = str(date.today())
                item['scraping_type'] = response.url.split('/')[-1]

                yield item
