# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
# import sqlite3
#
# con = None  # db connection
#
#
# class SQLitePipeline(object):
#     def __init__(self):
#         self.setupDBCon()
#         self.create()
#
#     def process_item(self, item, spider):
#         self.storeInDb(item)
#         return item
#
#     def storeInDb(self, item):
#         self.cur.execute("INSERT OR REPLACE INTO topnews(title,url,time) VALUES(?,?,?)",
#                          (item['title'], item['url'], item['time']))
#         self.con.commit()
#
#     def setupDBCon(self):
#         self.con = sqlite3.connect('topnews.db')
#         self.cur = self.con.cursor()
#
#     def __del__(self):
#         self.closeDB()
#
#     def create(self):
#         self.cur.execute("CREATE TABLE IF NOT EXISTS topnews(id INTEGER PRIMARY KEY \
#         AUTOINCREMENT NOT NULL, title STRING, url STRING UNIQUE ON CONFLICT REPLACE, time DATETIME);")
#
#     def closeDB(self):
#         self.con.close()

import json

class JsonWriterPipeline(object):

    def open_spider(self, spider):
        self.file = open('items_news.json', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + ",\n"
        self.file.write(line)
        return item
