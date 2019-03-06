import re

import sqlite3
import json

from text_processing.preprocess import preprocess
from text_processing.translate import translate
from xl_stats import write_rows_content, write_rows_title, write_topics
from googletrans import Translator


conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]
STOP_PATH = './text_processing/stop-words.txt'
with open(STOP_PATH,"r") as f:
    STOP_WORDS = f.read().split('\n')

def find_countries(data):
    c.execute("SELECT * FROM countries")
    all_rows = c.fetchall()
    to_remove = set()
    to_add = set()

    for ent in data:
        for row in all_rows:
            low = [w.lower() for w in row if w is not None]
            if ent:
                if ent.lower() in low:
                    to_remove.add(ent)
                    to_add.add(row[0])
                if len(ent) <= 1:
                    to_remove.add(ent)

    res = [w for w in data if w not in to_remove]
    res.extend(to_add)

    return ' '.join(res)


class Topic:

    def __init__(self, name, init_news, trend):

        self.name = name
        self.trend = trend

        self.news = init_news
        self.sentences_by_words = dict.fromkeys(self.name)

        self.main_words = []
        self.unique_words = {}

        for key in self.sentences_by_words:
            self.sentences_by_words[key] = []

        for word in self.name:
            for i, new in enumerate(self.news):
                for sent in new.sentences:
                    if word in sent:
                        self.sentences_by_words[word].append(sent)

        name_lower = {item for w in self.name for item in w.lower().split()}

        if self.trend:
            a = self.point_a()
        else:
            a = False
        # b = self.point_b()
        c = self.point_c()

        self.valid = a | c


        if not self.main_words:
            self.valid = False

        # Пункт б
        # Вариант с процентами
        # percent = 0
        #
        # for word in self.name:
        #     other_words = self.name - {word}
        #     first_words = {item for sublist in self.sentences_by_words[word] for item in sublist}
        #     for ow in other_words:
        #         second_words = {item for sublist in self.sentences_by_words[ow] for item in sublist}
        #         com_words = first_words.intersection(second_words)
        #         if com_words:
        #             self.main_words.extend(com_words)
        #             percent += 1
        #
        # percent /= len(self.name)*(len(self.name)-1)
        #
        # if percent >= 0.15:
        #     self.valid = True

    def point_a(self):

        # Пункт а
        # С названиями
        # com_words = {word.lower() for word in self.news[0].tokens['title']}.intersection(
        #             {w.lower() for w in self.news[1].tokens['title']})

        com_words = self.news[0].description.intersection(self.news[1].description)
        countries = {c for c in com_words if c in COUNTRIES}
        not_countries = com_words - countries
        if countries and not_countries:
            self.main_words.extend(com_words)
            return True

        return False

    def point_b(self):

        # Пункт б
        # Вариант "Или"

        count_words = 0

        for word in self.name:
            all_sent = [set(s.split()) for s in self.sentences_by_words[word]]
            if all_sent:
                com_words = set.intersection(*all_sent)
                com_words -= {word}
                if com_words:
                    count_words += 1
                    self.main_words.extend(com_words)

        # print('b', self.name, com_words)

        if count_words >= 2:
            return True
        return False

    def point_c(self):

        # Пункт в

        for new in self.news:
            cw_in_tokens = new.description.intersection(self.name)
            countries = {c for c in cw_in_tokens if c in COUNTRIES}
            not_countries = cw_in_tokens - countries
            if countries and not_countries:
                self.main_words.extend(countries)
                self.main_words.extend(not_countries)
                # print('c', self.name, countries, not_countries)
                return True
        return False


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

        self.unique_trends = []

        raw_data = self.c.fetchall()

        for i, row in enumerate(raw_data):
            doc = Document(i, row, self.conn, table)
            self.data.append(doc)

        for row1 in self.data:
            other_rows = [r for r in self.data if r.country != row1.country]
            self.frequencies[row1] = {row2: len(row1.description.intersection(row2.description))
                                 for row2 in other_rows}

    def find_trends(self):

        for row1 in self.data:
            maxim = max(self.frequencies[row1].values())
            if maxim != 0:

                most_similar = {key: value for key, value in self.frequencies[row1].items() if value == maxim}
                for ms in most_similar:
                    if self.frequencies[ms][row1] == max(self.frequencies[ms].values()):
                        mss = {row1, ms}

                        name = row1.description.intersection(ms.description)
                        countries = {w for w in name if w.upper() in COUNTRIES}
                        not_countries = name-countries

                        if countries and not_countries:
                            self.similarities.append(mss)
                            new_topic = Topic(name, list(mss), True)
                            self.trends.append(new_topic)

        write_topics("тренды до удаления.xlsx", self.trends)

        self.trends = [topic for topic in self.trends if topic.valid]

        write_topics("тренды после удаления.xlsx", self.trends)

    def find_topics(self):

        for row1 in self.data:
            maxim = max(self.frequencies[row1].values())
            if maxim != 0:
                most_similar = {key: value for key, value in self.frequencies[row1].items() if value == maxim}
                for ms in most_similar:
                        mss = {row1, ms}
                        name = row1.description.intersection(ms.description)

                        countries = {w for w in name if w.upper() in COUNTRIES}
                        not_countries = name - countries

                        if countries and len(not_countries) >= 2:
                            print("Success", row1.id, ms.id, name)

                            self.similarities.append(mss)
                            new_topic = Topic(name, list(mss), False)
                            self.topics.append(new_topic)
                        else:
                            print("Fail:", row1.id, ms.id, name)

        write_topics("темы до удаления.xlsx", self.topics)

        self.topics = [topic for topic in self.topics if topic.valid]

        write_topics("темы после удаления.xlsx", self.topics)

    def find_unique_trends(self):

        remove_trends = set()

        all_words = set()
        
        for trend in self.trends:
            all_words.update(trend.name)
        all_words_dict = dict.fromkeys(all_words,set())
        for key in all_words_dict.keys():
            for trend in self.trends:
                if key in trend.name:
                    all_words_dict[key].add(trend)

        for trend in self.trends:
            other_trends = [t for t in self.trends if t!=trend]
            for ot in other_trends:
                if trend.name == ot.name and not trend.news.intersection(ot.news):
                    remove_trends.add(trend)
                    remove_trends.add(ot)
                else:
                    com_words = trend.name.intersection(ot.name)
                    countries = {w for w in com_words if w.upper() in COUNTRIES}
                    not_countries = com_words - countries
                    if countries and not_countries:
                        for word in com_words:
                            if all_words_dict[word] == {trend, ot}:
                                news = list(set(trend.news).union(set(ot.news)))
                                new_trend = Topic(com_words, news, True)
                                new_trend.unique_words.append(word)
                                self.unique_trends.append(trend)



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
        self.description = self.tokens['title'].union(self.tokens['lead'])
        # self.title_without_countries = {d for d in self.tokens['title'] if d not in COUNTRIES}

        self.sentences = [find_countries(preprocess(sent)) for sent in self.translated['content'].split('. ')]

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


            self.named_entities[typ] = set()


            self.find_entities(typ, 'nes')

            self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ, 'nes')

            self.named_entities[typ].add(self.country.upper())
            self.tokens[typ].add(self.country.upper())

            cursor = self.conn.cursor()

            cursor.execute(f"UPDATE buffer SET tokens_{typ}=(?) WHERE reference=(?)",
                                (','.join(self.tokens[typ]), self.url))

            # self.unite_countries_in(typ, 'nes')

            # to_remove = set()
            #
            # for ent in self.named_entities[typ]:
            #     if ent == '' or ent.lower() in STOP_WORDS:
            #         to_remove.add(ent)
            #
            # self.named_entities[typ] -= to_remove


            # c.execute(f"UPDATE buffer SET nes_{typ}=(?) WHERE reference=(?)",
            #           (','.join(self.named_entities[typ]), self.url))
            # self.conn.commit()

            # self.find_entities(typ, 'tokens')
            # self.find_entities(typ, 'nes')
            # # self.unite_countries_in(typ, 'tokens')
            # self.unite_countries_in(typ,'nes')

            # for date in self.dates:
            #     self.named_entities['content'].add(date)

    def find_entities(self, ty, type_of_data):

            c = self.conn.cursor()

            c.execute(f"SELECT nes_{ty} FROM buffer WHERE reference=(?)", (self.url,))
            res = c.fetchone()[f"nes_{ty}"]
            if res:
                self.named_entities[ty] = set(res.split(','))

            else:
                print('s')

                text = re.findall(r"[\w]+|[^\s\w]", self.translated[ty])

                uppercase_words = []

                for i in range(len(text)):
                    if text[i][0].isupper() and text[i].lower() not in STOP_WORDS:
                        uppercase_words.append('the '+text[i])

                str_to_translate = '\n'.join(uppercase_words)
                with open("1.txt","w") as f:
                    f.write(str_to_translate)
                with open("1.txt", "r") as f:
                    str_to_translate = f.read()

                if str_to_translate:
                    eng = translate(str_to_translate, country_or_language='en')
                else:
                    eng = ''

                with open("2.txt","w") as f:
                    f.write(eng)
                with open("2.txt", "r") as f:
                    eng = f.read()

                if eng:
                    deu = translate(eng, country_or_language='de')
                else:
                    deu = ''

                with open("3.txt","w") as f:
                    f.write(deu)
                with open("3.txt", "r") as f:
                    deu = f.read()

                if deu:
                    eng1 = translate(deu, country_or_language='en')
                else:
                    eng1 = ''

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
                    elif 'das 'in uppercase_words_en[i]:
                        word = uppercase_words_en[i].replace('das ', '')
                    else:
                        word = uppercase_words_en[i]

                    if 'the ' in uppercase_words_en1[i]:
                        word1 = uppercase_words_en1[i].replace('the ', '')
                    elif 'der ' in uppercase_words_en1[i]:
                        word1 = uppercase_words_en1[i].replace('der ', '')
                    elif 'die ' in uppercase_words_en1[i]:
                        word1 = uppercase_words_en1[i].replace('die ', '')
                    elif 'das 'in uppercase_words_en1[i]:
                        word1 = uppercase_words_en1[i].replace('das ', '')
                    else:
                        word1 = uppercase_words_en1[i]

                    if word and word1:
                        if len(word) > 1 and word[0].isupper() and word == word1:
                            self.named_entities[ty].add(word)



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

    c.find_trends()
    c.find_topics()
    #
    # t = Tree(c)
    #
    # f = open("time1.txt", "w")
    # f.write(str(time.time()-now))