import nltk
from nltk.corpus import wordnet as wn
import string
import sqlite3
from datetime import date
import json
import operator


class Corpus(object):
    def __init__(self, time=date.today()):
        self.time = time

    def __iter__(self):
        data = json.load(open('scrapnews/spiders/items.json',encoding="utf8"))
        print(data)
        for item in data:
            yield item


# def tokenize(title):
#     tokens = nltk.word_tokenize(title)  # список слов в новости
#     for i in range(len(tokens)):
#         tokens[i] = tokens[i].lower()
#         if wn.morphy(tokens[i]) is not None:
#             tokens[i] = wn.morphy(tokens[i])  # используем morphy, чтобы убрать множ число и формы глаголов, а также понижаем регистр
#     return tokens


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


