import re

import sqlite3

from text_processing.preprocess import preprocess
from text_processing.translate import translate
from xl_stats import write_topics, write_news


conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]
STOP_PATH = './text_processing/stop-words.txt'
with open(STOP_PATH, "r") as f:
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

    def __init__(self, name, init_news):

        self.name = name
        self.new_name = self.name

        self.news = init_news
        self.sentences_by_words = dict.fromkeys(self.name)

        self.main_words = set()
        self.unique_words = set()

        for key in self.sentences_by_words:
            self.sentences_by_words[key] = []

        for word in self.name:
            for i, new in enumerate(self.news):
                for sent in new.sentences:
                    if word in sent:
                        self.sentences_by_words[word].append(sent)

        # name_lower = {item for w in self.name for item in w.lower().split()}

        a = self.point_a()

        self.valid = a

    def point_a(self):

        # Пункт а
        # С названиями

        com_words = self.news[0].description.intersection(self.news[1].description)

        # print('a', self.name, com_words)

        if count_countries(com_words) >= 1 and count_not_countries(com_words) >= 1 or count_not_countries(com_words) >= 2:
            self.main_words.update(com_words)
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
                    self.main_words.update(com_words)

        # print('b', self.name, com_words)

        if count_words >= 2:
            return True
        return False

    def point_c(self):

        # Пункт в

        for new in self.news:
            cw_in_tokens = new.description.intersection(self.name)

            if count_not_countries(cw_in_tokens):
                self.main_words.update(cw_in_tokens)
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

        raw_data = self.c.fetchall()

        for i, row in enumerate(raw_data):
            doc = Document(i, row, self.conn, table)
            self.data.append(doc)

        for row in self.data:
            self.frequencies[row] = {}

        for row1 in self.data:
            other_rows = [r for r in self.data if r.country != row1.country]

            for row2 in other_rows:
                cw = row1.named_entities['content'].intersection(row2.named_entities['content'])
                if count_countries(cw) >= 1 and count_not_countries(cw) >= 2:
                    self.frequencies[row1][row2] = len(cw)


    def find_topics(self):
        for row1 in self.data:
            try:
                maxim = max(self.frequencies[row1].values())
                if maxim != 0:
                    most_similar = {key: value for key, value in self.frequencies[row1].items() if value == maxim}
                    for ms in most_similar:
                            mss = {row1, ms}
                            name = row1.named_entities['content'].intersection(ms.named_entities['content'])

                            if mss not in self.similarities:

                                self.similarities.append(mss)
                                new_topic = Topic(name, list(mss))

                                self.topics.append(new_topic)
            except ValueError:
                continue

        self.topics = list(set(self.topics))



    def check_unique(self):
        for topic in self.topics:
            other_topics = [t for t in self.topics if t != topic]
            for ot in other_topics:
                cw = topic.name.intersection(ot.name)
                if count_countries(cw) >= 1 and count_not_countries(cw) >= 1:
                    continue
                else:
                    topic.new_name -= cw

        to_remove = set()
        for topic in self.topics:
            if not topic.name:
                to_remove.add(topic)
        self.topics = [t for t in self.topics if t not in to_remove]

    def find_identic_topics(self):


        all_names = {frozenset(topic.name) for topic in self.topics}

        temporary = []

        topic_dict = dict.fromkeys(all_names, set())

        for key in topic_dict.keys():
            topic_dict[key] = {t for t in self.topics if t.name==key}


        for key, value in topic_dict.items():

            if len(value) >= 2:

                    com_words = set.intersection(*[t.main_words for t in value])

                    if count_countries(com_words) >= 1 and count_not_countries(com_words) >= 2:
                        news = {new for topic in value for new in topic.news}
                        new_topic = Topic(key, list(news))
                        self.topics.append(new_topic)
                        for v in value:
                            self.topics.remove(v)
                    else:
                        temporary.append(value)

        for value in temporary:

            for t in value:
                name = t.name

            unique_words = name.copy()

            for key in all_names:
                if not name.issubset(key):
                    unique_words -= key


            if count_not_countries(unique_words) >= 2:
                news = {new for topic in value for new in topic.news}
                new_topic = Topic(name, list(news))
                self.topics.append(new_topic)
                for t in value:
                    if t in self.topics:
                        self.topics.remove(t)
            else:
                for t in value:
                    if t in self.topics:
                        self.topics.remove(t)


    def delete_small(self):
        all_names = {frozenset(topic.name) for topic in self.topics}
        self.topics.sort(key=lambda t: -len(t.name))
        to_remove = set()

        for topic in self.topics:
            if any(topic.name.issubset(other) for other in all_names if topic.name != other):
                print(topic.name)
                to_remove.add(topic)

        self.topics = [t for t in self.topics if t not in to_remove]


    def find_unique(self):

        self.trends = []

        all_names = {frozenset(topic.name) for topic in self.topics}
        for t in self.topics:

            unique_words = t.name.copy()

            for key in all_names:
                if not t.name.issubset(key):
                    unique_words -= key

            print(unique_words)

            if unique_words:
                t.main_words = unique_words
                self.trends.append(t)

    def final_delete(self):
        to_remove = set()
        for topic in self.topics:
            if count_not_countries(topic.name) < 2:
                to_remove.add(topic)
        self.topics = [t for t in self.topics if t not in to_remove]





def count_countries(name):
    countries = {w for w in name if w.upper() in COUNTRIES}
    return len(countries)

def count_not_countries(name):
    countries = {w for w in name if w.upper() in COUNTRIES}
    not_countries = name - countries
    return len(not_countries)

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
        # self.title_without_countries = {d for d in self.tokens['title'] if d not in COUNTRIES}

        self.sentences = [find_countries(preprocess(sent)) for sent in self.translated['content'].split('. ')]



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

            self.named_entities[typ] = set()
            self.find_entities(typ, 'nes')

            self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ, 'nes')

            self.named_entities[typ].add(self.country.upper())
            self.tokens[typ].add(self.country.upper())

            # self.unite_countries_in(typ, 'nes')

            # to_remove = set()
            #
            # for ent in self.named_entities[typ]:
            #     if ent == '' or ent.lower() in STOP_WORDS:
            #         to_remove.add(ent)
            #
            # self.named_entities[typ] -= to_remove

            c.execute(f"UPDATE buffer SET nes_{typ}=(?), tokens_{typ}=(?) WHERE reference=(?)",
                      (','.join(self.named_entities[typ]), ','.join(self.tokens[typ]), self.url))
            self.conn.commit()

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

                text = re.findall(r"[\w]+|[^\s\w]", self.translated[ty])

                uppercase_words = set()

                for i in range(len(text)-2):
                    if text[i][0].isupper() and text[i].lower() not in STOP_WORDS:
                        word = text[i]
                        text[i] = ' '


                        if  text[i+1][0].isupper() and text[i+1].lower() not in STOP_WORDS:

                                word = word + ' ' + text[i + 1]
                                text[i + 1] = ' '

                                if text[i+2][0].isupper() and text[i+2].lower() not in STOP_WORDS:

                                        word = word + ' ' + text[i + 2]
                                        text[i + 2] = ' '

                                if self.translated[ty].count(word) > 1:
                                    uppercase_words.add('the '+word)
                                else:
                                    elems = word.split()
                                    flag = True
                                    for el in elems:
                                        if self.translated[ty].count(el) > 1:
                                            flag = False
                                            uppercase_words.add('the '+el)
                                    if flag is True:
                                        uppercase_words.add('the ' + word)
                        uppercase_words.add('the '+word)

                str_to_translate = '\n'.join(uppercase_words)

                with open("1.txt","w") as f:
                    f.write(str_to_translate)
                with open("1.txt", "r") as f:
                    str_to_translate = f.read()

                eng = translate(str_to_translate, arg='en')

                with open("2.txt","w") as f:
                    f.write(eng)
                with open("2.txt", "r") as f:
                    eng = f.read()

                deu = translate(eng, arg='de')

                with open("3.txt","w") as f:
                    f.write(deu)
                with open("3.txt", "r") as f:
                    deu = f.read()

                eng1 = translate(deu, arg='en')

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

                self.named_entities[ty] = delete_duplicates(self.named_entities[ty])



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
            deu_text = translate(eng_text, self.country)
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


def delete_duplicates(text):
    to_remove = set()
    for word in text:
        others = text - {word}
        for o in others:
            if word in o:
                to_remove.add(o)
    text = text - to_remove
    return text


if __name__ == '__main__':

    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    c = Corpus(db, table)

    # c.find_trends()
    c.find_topics()
    write_topics("темы-1.xlsx", c.topics)
    c.check_unique()
    write_topics("темы-2.xlsx", c.topics)
    for topic in c.topics:
        topic.name = topic.new_name
    c.delete_small()
    write_topics("темы-3.xlsx", c.topics)
    c.find_identic_topics()
    write_topics("темы-4.xlsx", c.topics)

    c.final_delete()
    write_topics("темы-5.xlsx", c.topics)


    #
    # t = Tree(c)
    #
    # f = open("time1.txt", "w")
    # f.write(str(time.time()-now))