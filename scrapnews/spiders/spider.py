import scrapy
from googletrans import Translator
from scrapnews.items import NewsItem
from datetime import date

countries = {'au': 'Australia',
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

class NewsSpider(scrapy.Spider):
    name = "news"

    start_urls = list()
    time = 'day'
    for country in countries.keys():
        start_urls.append('https://top.st/' + country + "/" + time)

    def translate(self, corpus):
        t = Translator()
        for text in corpus:
            yield t.translate(text).text

    def parse(self, response):
        for i,new in enumerate(response.css('h2')):
            item = NewsItem()
            all_titles = new.css('a::text').extract()
            co = response.url.split('/')[-2]
            if co not in ('gb','us'):
                all_titles = self.translate(all_titles)
            for title in all_titles:
                item['number'] = i+1
                item['title'] = title
                item['url'] = new.css('a::attr(href)').extract_first()
                item['time'] = date.today()
                item['country'] = countries[co]
                yield item