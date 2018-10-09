import nltk
from nltk.corpus import wordnet as wn
import string
import sqlite3
from datetime import date
import json
import operator
from document import Document
from corpus import add_column


# class Corpus(object):
#     def __init__(self, time=date.today()):
#         self.time = time
#
#     def __iter__(self):
#         data = json.load(open('scrapnews/spiders/items.json',encoding="utf8"))
#         print(data)
#         for item in data:
#             yield item

class Corpus:

    def __init__(self, db, table):

        self.db = db
        self.table = table
        self.conn = sqlite3.connect(f"db/{db}.db")
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.c.execute("SELECT * FROM " + table)
        self.topics = []
        self.data = []
        self.trends = []
        self.similarities = []
        self.frequencies = {}

        raw_data = self.c.fetchall()

        try:
            self.create_documents(raw_data)

        except IndexError:
            self.create_columns_and_documents(raw_data)

    def create_documents(self, data):
        for i, row in enumerate(data):
            doc = Document(i, row, self.conn, self.table)
            self.data.append(doc)

    def create_columns_and_documents(self, raw_data):
        add_column(self.table, 'translated', 10000, self.c)
        add_column(self.table, 'translated1', 10000, self.c)
        add_column(self.table, 'translated_lead', 1000, self.c)
        add_column(self.table, 'translated1_lead', 1000, self.c)
        add_column(self.table, 'translated_title', 1000, self.c)
        add_column(self.table, 'translated1_title', 1000, self.c)
        add_column(self.table, 'nes_content', 1000, self.c)
        add_column(self.table, 'nes_lead', 1000, self.c)
        add_column(self.table, 'nes_title', 1000, self.c)
        add_column(self.table, 'tokens_content', 10000, self.c)
        add_column(self.table, 'tokens_lead', 1000, self.c)
        add_column(self.table, 'tokens_title', 1000, self.c)
        self.conn.commit()
        self.create_documents(raw_data)



com_words = list()
class Topnews(object):
    def __init__(self, data, mweight):
        self.data = data
        self.tokens = [d['tokens'].split(' ') for d in data]
        self.edges = []
        self.mweight = mweight
        self.preprocess()

    def preprocess(self):

        for i in range(len(self.tokens)):
            for j in range(i+1, len(self.tokens)):
                #if self.tokens[i][0] != self.tokens[j][0]:
                weight = 0
                for tk in self.tokens[i]:
                    if tk in self.tokens[j]:
                        com_words.append(tk)
                        weight += 1
                if weight > self.mweight:
                    self.edges.append((i, j ,weight))

        # for word in com_words:
        #     if word not in frequencies.keys():
        #         frequencies[word] = 1
        #     else:
        #         frequencies[word] += 1
        #
        # with open('max.txt','w') as f:
        #     for item in sorted(frequencies.items(), key=operator.itemgetter(1), reverse=True):
        #         f.write(str(item)+'\n')


