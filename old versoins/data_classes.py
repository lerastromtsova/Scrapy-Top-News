import re
import nltk
import os

import sqlite3

from text_processing.preprocess import preprocess
from text_processing.translate import translate
from text_processing.dates import process_dates
from xl_stats import write_rows



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

        raw_data = self.c.fetchall()

        for i,row in enumerate(raw_data):
            doc = Document(i,row, self.conn, table)
            self.data.append(doc)

    def find_topics(self):

        # for row1 in self.data:
        #     rows_except_this = [r for r in self.data if r.url != row1.url and r.country != row1.country]
        #     for row2 in rows_except_this:
        #         com_words = row1.named_entities['content'].intersection(row2.named_entities['content'])
        #         # com_words = row1.tokens['title'].intersection(row2.tokens['title'])
        #         if len(com_words) and com_words not in self.topics:
        #             self.topics.append(com_words)

        # self.topics.sort(key=lambda s: -len(s))
        similarities = []
        frequencies = {}


        for row1 in self.data:
            other_rows = [r for r in self.data if r.country != row1.country]
            frequencies[row1] = {row2: len(row1.named_entities['content'].intersection(row2.named_entities['content'])) for row2 in other_rows}

        for row1 in self.data:
            maxim = max(frequencies[row1].values())
            if maxim != 0:
                most_similar = {key: value for key, value in frequencies[row1].items() if value == maxim}
                for ms in most_similar:
                    if frequencies[ms][row1] == max(frequencies[ms].values()):
                        mss = {row1,ms}
                        if len(mss) > 1 and mss not in similarities:
                            similarities.append(mss)

        write_rows("sim_topics.xlsx", similarities)

    def delete_news(self):

        print(len(self.data))

        remove = set()

        for doc in self.data:
            links = {}
            for doc1 in self.data:
                com_words = doc.description.intersection(doc1.description)
                links[' '.join(com_words)] = len(com_words)
            print(links)
            if max(links.values()) == 1:
                was_equal = False
                coms = list(links.keys())
                for i in range(len(coms)-1):
                    for j in range(i+1,len(coms)):
                        if coms[i]==coms[j]:
                            was_equal = True
                if not was_equal:
                    remove.add(doc)

        self.data = [d for d in self.data if d not in remove]
        print(len(self.data))


class Document:

    def __init__(self, id, row, conn, table):

        self.id = id

        types = ('title', 'lead', 'content')
        self.raw = row

        self.country = row['country']
        self.date = row['date']
        self.orig_data = dict.fromkeys(types)
        self.orig_data['title'] = row['title']

        try:
            self.orig_data['lead'] = row['lead']
        except IndexError:
            self.orig_data['lead'] = row['description']

        self.orig_data['content'] = row['content']
        self.url = row['reference']

        self.translated = dict.fromkeys(types)
        self.double_translated = dict.fromkeys(types)
        self.tokens = dict.fromkeys(types)
        self.named_entities = dict.fromkeys(types)

        self.conn = conn
        self.table = table

        self.dates = process_dates(list(self.tokens)).append(self.date)
        self.process(['title', 'lead', 'content'])
        self.description = self.tokens['title'].union(self.named_entities['lead'])

    def process(self, arr_of_types):

        for typ in arr_of_types:

            if typ == 'content':
                col = 'translated'
                col1 = 'translated1'

            else:
                col = f'translated_{typ}'
                col1 = f'translated1_{typ}'

            if self.raw[col]:
                self.translated[typ] = self.raw[col]
            else:
                self.double_translate(typ)

            if self.raw[col1]:
                self.double_translated[typ] = self.raw[col1]
            else:
                self.double_translate(typ)

            self.tokens[typ] = {word for word in preprocess(self.translated[typ]) if
                                word in preprocess(self.double_translated[typ])}

            self.named_entities[typ] = self.tokens[typ]


            parse_tree = nltk.ne_chunk(nltk.tag.pos_tag(self.named_entities[typ]),
                                       binary=True)  # POS tagging before chunking!

            self.named_entities[typ] = {k[0] for branch in parse_tree.subtrees() for k in list(branch) if branch.label() == 'NE'}

            self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ,'nes')
            self.find_entities(typ, 'tokens')
            self.find_entities(typ, 'nes')
            self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ,'nes')

            # for date in self.dates:
            #     self.named_entities['content'].add(date)

    def find_entities(self, ty, type_of_data):

        text = re.findall(r"[\w]+|[^\s\w]", self.translated[ty])

        to_remove = set()
        to_add = set()
        if type_of_data == 'nes':
            nes = self.named_entities[ty]
        elif type_of_data == 'tokens':
            nes = self.tokens[ty]

        for ent1 in nes:
            if ent1 in text:
                idx1 = text.index(ent1)
                entities_except_this = nes - set(ent1)

                for ent2 in entities_except_this:
                    if ent2 in text:
                        idx2 = text.index(ent2)
                        if ent1[0].isupper() and ent2[0].isupper() and (((idx2 - idx1 == 2) and (text[idx1+1] == ' ' or text[idx1+1] == '-'
                                                    or text[idx1+1] == "'" or text[idx1+1] == 'of')) or idx2 - idx1 == 1):

                            united_entity = ' '.join([ent1, ent2])
                            to_add.add(united_entity)
                            to_remove.add(ent1)
                            to_remove.add(ent2)

        if type_of_data == 'nes':
            self.named_entities[ty] = (self.named_entities[ty] - to_remove) | to_add
        elif type_of_data == 'tokens':
            self.tokens[ty] = (self.tokens[ty] - to_remove) | to_add

    def unite_countries_in(self, ty, type_of_data):
        conn = sqlite3.connect("db/countries.db")
        c = conn.cursor()
        c.execute("SELECT * FROM countries")
        all_rows = c.fetchall()
        to_remove = set()
        to_add = set()
        if type_of_data == "nes":
            data = self.named_entities[ty]
        elif type_of_data=='tokens':
            data = self.tokens[ty]
        for ent in data:
                for row in all_rows:
                    low = [w.lower() for w in row if w is not None]
                    if ent.lower() in low:
                        to_remove.add(ent)
                        to_add.add(row[0])

        if type_of_data == 'nes':
            self.named_entities[ty] = (self.named_entities[ty] - to_remove) | to_add
        elif type_of_data == 'tokens':
            self.tokens[ty] = (self.tokens[ty] - to_remove) | to_add

    def double_translate(self, ty):

        n = 1500  # length limit
        text = self.orig_data[ty]
        self.translated[ty] = ''
        self.double_translated[ty] = ''

        if "Краткое описание: " in text:
            text = text.split("Краткое описание: ")[1]

        # Split into parts of 1500 before translating
        text = [text[i:i + n] for i in range(0, len(text), n)]

        for part in text:

            eng_text = translate(part)
            orig_text = translate(eng_text, self.country)
            eng1_text = translate(orig_text)

            self.translated[ty] += ' '
            self.translated[ty] += eng_text
            self.double_translated[ty] += ' '
            self.double_translated[ty] += eng1_text

        c = self.conn.cursor()
        if ty == 'content':
            col = 'translated'
            col1 = 'translated1'

        else:
            col = f'translated_{ty}'
            col1 = f'translated1_{ty}'

        c.execute(f"UPDATE {self.table} SET {col}=(?), {col1}=(?) WHERE reference=(?)",
                  (self.translated[ty], self.double_translated[ty], self.url))
        self.conn.commit()

if __name__ == '__main__':

    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    c = Corpus(db, table)
    c.find_topics()