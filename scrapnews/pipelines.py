# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3

con = None  # db connection


class SQLitePipeline(object):
    def __init__(self):
        self.setupDBCon()
        self.create()

    def process_item(self, item, spider):
        self.storeInDb(item)
        return item

    def storeInDb(self, item):
        self.cur.execute("INSERT OR REPLACE INTO topnews(url, title, number, country, tokens, scraping_date, scraping_type) \
                          VALUES(?,?,?,?,?,?,?)",
                         (item['url'], item['title'],
                          item['number'], item['country'],
                          item['tokens'], item['scraping_date'],
                          item['scraping_type']))
        self.con.commit()

    def setupDBCon(self):
        self.con = sqlite3.connect('topnews.db')
        self.cur = self.con.cursor()

    def __del__(self):
        self.closeDB()

    def create(self):
        self.cur.execute("CREATE TABLE IF NOT EXISTS topnews(id INTEGER PRIMARY KEY \
        AUTOINCREMENT NOT NULL, url STRING UNIQUE ON CONFLICT REPLACE, title STRING, \
        number STRING, country STRING, tokens STRING, scraping_date DATETIME, scraping_type STRING);")

    def closeDB(self):
        self.con.close()

class VisualisationPipeline(object):

    def process_item(self, item, spider):
        print("Process",item)