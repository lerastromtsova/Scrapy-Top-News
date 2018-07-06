import re
import nltk

import sqlite3
from pandas import DataFrame

from text_processing.preprocess import preprocess
from text_processing.translate import translate
from text_processing.dates import process_dates
from xl_stats import write_rows
from googletrans import Translator


conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]
STOP_PATH = './text_processing/stop-words.txt'
with open(STOP_PATH,"r") as f:
    STOP_WORDS = f.read().split('\n')

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
            doc = Document(i, row, self.conn, table)
            self.data.append(doc)

    def find_topics(self):

        similarities = []
        frequencies = {}

        for row1 in self.data:
            other_rows = [r for r in self.data if r.country != row1.country]
            frequencies[row1] = {row2: len(row1.named_entities['content'].intersection(row2.named_entities['content']))
                                 for row2 in other_rows}

        for row1 in self.data:
            maxim = max(frequencies[row1].values())
            if maxim != 0:
                most_similar = {key: value for key, value in frequencies[row1].items() if value == maxim}
                for ms in most_similar:
                    if frequencies[ms][row1] == max(frequencies[ms].values()):
                        mss = {row1, ms}
                        if len(mss) > 1 and mss not in similarities:
                            similarities.append(mss)

        write_rows("sim_topics.xlsx", similarities)

t = Translator()

class Document:

    def __init__(self, id, row, conn, table):

        types = ('title','lead','content')
        self.id = id
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

        # self.dates = process_dates(list(self.tokens)).append(self.date)
        self.process(['title','lead','content'])
        # self.description = self.tokens['title'].union(self.named_entities['lead'])
        # self.descr_without_countries = {d for d in self.description if d not in COUNTRIES}

    def process(self, arr_of_types):

        for typ in arr_of_types:

            if typ == 'content':
                col = 'translated'
                col1 = 'translated1_d'

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

            self.named_entities[typ] = set()
            if typ =='content':
                self.named_entities[typ].add(self.country)

            self.find_entities(typ, 'nes')

            # self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ, 'nes')
            # self.find_entities(typ, 'tokens')
            # self.find_entities(typ, 'nes')
            # # self.unite_countries_in(typ, 'tokens')
            # self.unite_countries_in(typ,'nes')

            # for date in self.dates:
            #     self.named_entities['content'].add(date)

    def find_entities(self, ty, type_of_data):

            c = self.conn.cursor()
            #
            # c.execute(f"SELECT nes_{ty} FROM buffer WHERE reference=(?)", (self.url,))
            # res = c.fetchone()[f"nes_{ty}"]
        # if res:
        #     self.named_entities[ty] = set(res.split(','))
        # else:

            text = re.findall(r"[\w]+|[^\s\w]", self.translated[ty])

            uppercase_words = []

            for i in range(len(text)-4):

                    if text[i][0].isupper() and text[i].lower() not in STOP_WORDS:
                            word = text[i]

                            if text[i+1] == '-':
                                word += f" {text[i+2]}"
                                text[i+2] = ' '
                                if text[i+3] =='-':
                                    word += f" {text[i+4]}"
                                    text[i + 4] = ' '
                                elif text[i+3][0].isupper() and text[i+3].lower() not in STOP_WORDS:
                                    word += f" {text[i+3]}"
                                    text[i + 3] = ' '

                            elif text[i+1][0].isupper() and text[i+1].lower() not in STOP_WORDS:
                                word += f" {text[i+1]}"
                                text[i + 1] = ' '
                            uppercase_words.append('the '+word)

            str_to_translate = '\n'.join(uppercase_words)
            with open("1.txt","w") as f:
                f.write(str_to_translate)
            with open("1.txt", "r") as f:
                str_to_translate = f.read()
            eng = t.translate(str_to_translate, dest='en').text
            with open("2.txt","w") as f:
                f.write(eng)
            with open("2.txt", "r") as f:
                eng = f.read()
            deu = t.translate(eng, dest='de').text
            with open("3.txt","w") as f:
                f.write(deu)
            with open("3.txt", "r") as f:
                deu = f.read()
            eng1 = t.translate(deu, dest='en').text
            with open("4.txt","w") as f:
                f.write(eng1)
            uppercase_words_en = eng.split('\n')
            uppercase_words_en1 = eng1.split('\n')
            for i in range(len(uppercase_words_en)):
                if 'the ' in uppercase_words_en[i]:
                    word = uppercase_words_en[i].replace('the ', '')
                elif 'der ' in uppercase_words_en[i]:
                    word = uppercase_words_en[i].replace('der ', '')
                elif 'die ' in uppercase_words_en[i]:
                    word = uppercase_words_en[i].replace('die ', '')
                else:
                    word = uppercase_words_en[i]

                if 'the ' in uppercase_words_en1[i]:
                    word1 = uppercase_words_en[i].replace('the ', '')
                elif 'der ' in uppercase_words_en1[i]:
                    word1 = uppercase_words_en[i].replace('der ', '')
                elif 'die ' in uppercase_words_en1[i]:
                    word1 = uppercase_words_en[i].replace('die ', '')
                else:
                    word1 = uppercase_words_en1[i]

                if word and word1:
                    if word[0].isupper() and word == word1:
                        self.named_entities[ty].add(word)

            c.execute(f"UPDATE buffer SET nes_{ty}=(?) WHERE reference=(?)", (','.join(self.named_entities[ty]), self.url))


    def unite_countries_in(self, ty, type_of_data):
        conn = sqlite3.connect("db/countries.db")
        c = conn.cursor()
        c.execute("SELECT * FROM countries")
        all_rows = c.fetchall()
        to_remove = set()
        to_add = set()
        if type_of_data == "nes":
            data = self.named_entities[ty]
        elif type_of_data == 'tokens':
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
            deu_text = translate(eng_text, 'Germany')
            eng1_text = translate(deu_text)

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


def find_all_upper(st):
    text = ''
    i = 0
    word = st[i]
    while word[0].isupper():
        text += f"{word} "
        i += 1
        word = st[i]

    return text

if __name__ == '__main__':

    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    c = Corpus(db, table)

    c.find_topics()
    #
    # t = Tree(c)
    #
    # f = open("time1.txt", "w")
    # f.write(str(time.time()-now))