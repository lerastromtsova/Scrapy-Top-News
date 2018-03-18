# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class NewsItem(Item):
    number = Field()
    title = Field()
    lead = Field()
    url = Field()
    time = Field()
    country = Field()
