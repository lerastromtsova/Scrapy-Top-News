# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class NewsItem(Item):
    url = Field()
    title = Field()
    # content = Field()
    number = Field()
    country = Field()
    tokens = Field()
    scraping_date = Field()
    scraping_type = Field()
    # news_date = Field()
