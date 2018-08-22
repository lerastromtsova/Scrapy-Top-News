from text_processing.preprocess import preprocess
from text_processing.translate import translate
import re
import nltk
import sqlite3


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
        self.c = self.conn.cursor()

        self.table = table

        # self.dates = process_dates(list(self.tokens)).append(self.date)
        self.process(['title','lead','content'])
        self.description = self.tokens['title'].union(self.tokens['lead'])


        # self.description.update(self.named_entities['title'])
        # self.description.update(self.named_entities['lead'])

        self.descr_with_countries = set()
        # self.title_without_countries = {d for d in self.tokens['title'] if d not in COUNTRIES}

        self.sentences = [replace_countries(preprocess(sent)) for sent in self.translated['content'].split('. ')]

        self.countries = {w for w in self.named_entities['content'] if w in COUNTRIES}
        self.descr_with_countries = self.description.union(self.countries)

        self.all_text = self.description.copy()
        self.all_text.update(self.named_entities['content'])



    def process(self, arr_of_types):
        c = self.conn.cursor()
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

            c.execute(f"SELECT tokens_{typ} FROM buffer WHERE reference=(?)", (self.url,))
            res = c.fetchone()[f"tokens_{typ}"]

            if res:
                self.tokens[typ] = set(res.split(','))
            else:
                self.tokens[typ] = {word for word in preprocess(self.translated[typ]) if
                                    word in preprocess(self.double_translated[typ])}

            tokens_copy = self.tokens[typ].copy()

            for w in self.tokens[typ]:
                word = w.replace("í", "i")
                tokens_copy.remove(w)
                tokens_copy.add(word)

            self.tokens[typ] = tokens_copy

            self.named_entities[typ] = find_countries(self.tokens[typ])

            self.find_entities(typ, 'nes')

            self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ, 'nes')

            self.named_entities[typ].add(self.country.upper())
            self.tokens[typ].add(self.country.upper())

            for t in self.tokens[typ]:
                if t[0].isupper() and any(char.isdigit() for char in t):
                    self.named_entities[typ].add(t)

            to_remove = set()

            for ent in self.named_entities[typ]:
                if ent == '' or ent.lower() in STOP_WORDS:
                    to_remove.add(ent)

            self.named_entities[typ] -= to_remove

            c.execute(f"UPDATE buffer SET nes_{typ}=(?), tokens_{typ}=(?) WHERE reference=(?)",
                      (','.join(self.named_entities[typ]), ','.join(self.tokens[typ]), self.url))
            self.conn.commit()

            # for date in self.dates:
            #     self.named_entities['content'].add(date)

    def find_entities(self, ty, type_of_data):

            c = self.conn.cursor()

            c.execute(f"SELECT nes_{ty} FROM buffer WHERE reference=(?)", (self.url,))
            res = c.fetchone()[f"nes_{ty}"]

            if res:

                for ent in res.split(','):
                    word = ent.replace("í", "i")
                    self.named_entities[ty].add(word)

                #self.named_entities[ty] = set(res.split(','))

            else:

                text = re.findall(r"[\w]+|[^\s\w]", self.translated[ty])

                uppercase_words = []

                for word in text:
                    if word[0].isupper():
                        if word.lower() not in STOP_WORDS:
                            uppercase_words.append('Why did ' + word.lower() + ' say?')

                uppercase_words.sort(reverse=True)

                str_to_translate = '\n'.join(uppercase_words)

                with open("text_processing/1.txt", "w") as f:
                    f.write(str_to_translate)
                with open("text_processing/1.txt", "r") as f:
                    str_to_translate = f.read()

                eng = translate(str_to_translate, arg='en')

                with open("text_processing/2.txt", "w") as f:
                    f.write(eng)
                with open("text_processing/2.txt", "r") as f:
                    eng = f.read()

                deu = translate(eng, arg='de')

                with open("text_processing/3.txt", "w") as f:
                    f.write(deu)
                with open("text_processing/3.txt", "r") as f:
                    deu = f.read()

                eng1 = translate(deu, arg='en')

                uppercase_words_en = eng.split('\n')
                uppercase_words_en1 = eng1.split('\n')

                for i in range(len(uppercase_words_en)):
                    try:
                        w = uppercase_words_en[i].split()[-2]
                        w1 = uppercase_words_en1[i].split()[-2]
                        if w and w1:

                            if len(w) > 1 and w1[0].isupper() and w.lower() == w1.lower():
                                self.named_entities[ty].add(w1)
                    except IndexError:
                        continue

                # self.named_entities[ty] = delete_duplicates(self.named_entities[ty])

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
                    if ent:
                        if ent.lower() in low:
                            to_remove.add(ent)
                            to_add.add(row[0])
                        if len(ent) <= 1:
                            to_remove.add(ent)
                        if ent.lower() == 'state':
                            to_remove.add(ent)
                            if self.country == 'United Kingdom':
                                to_add.add("UNITED STATES")
                    if len(ent.lower().split()) > 1:
                        for e in ent.lower().split():
                            if e in low:
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
            deu_text = translate(eng_text, 'de')
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


def find_countries(data):
    countries = set()

    for ent in data:
        for row in all_rows:
            low = [w.lower() for w in row if w is not None]
            if ent:
                if ent.lower() in low:
                    countries.add(row[0])


    return countries

def replace_countries(data):
    to_remove = set()
    to_add = set()
    for ent in data:
        for row in all_rows:
            low = [w.lower() for w in row if w is not None]
            if ent:
                if ent.lower() in low:
                    to_remove.add(ent)
                    to_add.add(row[0])

    data = [d for d in data if d not in to_remove]
    data.extend(to_add)
    return ' '.join(data)

def delete_duplicates(text):
    to_remove = set()
    for word in text:
        others = text - {word}
        for o in others:
            if word.lower() in o.lower():
                to_remove.add(word)
    text = text - to_remove
    return text


STOP_PATH = './text_processing/stop-words.txt'
with open(STOP_PATH, "r") as f:
    STOP_WORDS = f.read().split('\n')

conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]