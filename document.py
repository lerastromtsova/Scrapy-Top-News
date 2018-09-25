from text_processing.preprocess import preprocess, check_first_entities, replace_special_symbols, unite_countries_in
from text_processing.translate import translate
import re
import sqlite3
from string import punctuation


PUNKTS = ["''",'``','...','’','‘','-','“','"','—','”','–','–––','––']
TITLES = {"President", "Chancellor", "Democrat", "Governor", "King", "Queen", "Ministry", "Minister", "Prime", "The", "Federation"}
PREPS = ['at', 'on', 'in', 'by', 'of', 'to', 'is']


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
        self.sentences = []
        self.first_words = {}

        self.conn = conn
        self.c = self.conn.cursor()

        self.table = table
        self.process(['title', 'lead', 'content'])

        self.description = self.tokens['title'].union(self.tokens['lead'])
        self.descr_with_countries = set()

        self.countries = {w for w in self.named_entities['content'] if w in COUNTRIES}
        self.descr_with_countries = self.description.union(self.countries)

        self.all_text = self.description.copy()
        self.all_text.update(self.named_entities['content'])

        self.all_text_splitted = re.findall(r"[\w]+|[^\s\w]", self.translated["title"])
        self.all_text_splitted.extend(re.findall(r"[\w]+|[^\s\w]", self.translated["lead"]))
        self.all_text_splitted.extend(re.findall(r"[\w]+|[^\s\w]", self.translated["content"]))

        text = [w for w in self.all_text_splitted if len(w) >= 1 or w in punctuation or w in PUNKTS]

        self.uppercase_sequences = find_all_uppercase_sequences(text)
        self.numbers = {w for w in self.all_text_splitted if w.isdigit()}

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

            self.translated[typ] = replace_special_symbols(self.translated[typ])
            self.double_translated[typ] = replace_special_symbols(self.double_translated[typ])

            c.execute(f"SELECT tokens_{typ} FROM buffer WHERE reference=(?)", (self.url,))
            res = c.fetchone()[f"tokens_{typ}"]

            if res:
                self.tokens[typ] = set(res.split(','))
                self.tokens[typ] = {w for w in self.tokens[typ] if w not in STOP_WORDS}
            else:
                self.tokens[typ] = {word for word in preprocess(self.translated[typ]) if
                                    word in preprocess(self.double_translated[typ])}

            self.tokens[typ] = set(replace_special_symbols(' '.join(self.tokens[typ])).split())

            if "US" in self.translated[typ]:
                self.tokens[typ].add("UNITED_STATES")

            tokens_copy = self.tokens[typ].copy()

            self.tokens[typ] = tokens_copy

            self.named_entities[typ] = find_countries(self.tokens[typ])
            self.named_entities[typ] = set(replace_special_symbols(' '.join(self.named_entities[typ])).split())

            self.find_entities(typ, 'nes')

            self.unite_countries_in(typ, 'tokens')
            self.unite_countries_in(typ, 'nes')
            # self.translated[typ] = unite_countries_in(self.translated[typ])
            # self.double_translated[typ] = unite_countries_in(self.double_translated[typ])

            self.named_entities[typ].add(self.country.upper())
            self.tokens[typ].add(self.country.upper())

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

                        self.named_entities[ty].add(ent)

                # self.named_entities[ty] = set(res.split(','))

            else:

                text = re.findall(r"[\w]+|[^\s\w]", self.translated[ty])

                self.sentences.extend([replace_countries(preprocess(sent)) for sent in
                                  self.translated[ty].split('. ')])
                self.first_words.update(check_first_entities(
                    [sent.split()[0] if sent and sent[1][0].islower() else '' for sent in self.sentences]))

                # uppercase_words = []

                for word in text:
                    if word[0].isupper():
                        if word.lower() not in STOP_WORDS:
                            if word not in self.first_words.keys():
                                self.named_entities[ty].add(word)
                            else:
                                if self.first_words[word]:
                                    self.named_entities[ty].add(word)

                # uppercase_words.sort(reverse=True)
                #
                # str_to_translate = '\n'.join(uppercase_words)

                # with open("text_processing/1.txt", "w", encoding="utf-8") as f:
                #     f.write(str_to_translate)
                # with open("text_processing/1.txt", "r", encoding="utf-8") as f:
                #     str_to_translate = f.read()
                #
                # eng = translate(str_to_translate, arg='en')
                #
                # with open("text_processing/2.txt", "w", encoding="utf-8") as f:
                #     f.write(eng)
                # with open("text_processing/2.txt", "r", encoding="utf-8") as f:
                #     eng = f.read()
                #
                # deu = translate(eng, arg='de')
                #
                # with open("text_processing/3.txt", "w", encoding="utf-8") as f:
                #     f.write(deu)
                # with open("text_processing/3.txt", "r", encoding="utf-8") as f:
                #     deu = f.read()
                #
                # eng1 = translate(deu, arg='en')
                #
                # uppercase_words_en = eng.split('\n')
                # uppercase_words_en1 = eng1.split('\n')

                # for i in range(len(uppercase_words_en)):
                #     try:
                #         w = uppercase_words_en[i].split()[-2]
                #         w1 = uppercase_words_en1[i].split()[-2]
                #         if w and w1:
                #
                #             if len(w) > 1 and w1[0].isupper() and w.lower() == w1.lower():
                #                 self.named_entities[ty].add(w1)
                #     except IndexError:
                #         continue

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

        n = 1000  # length limit
        text = self.orig_data[ty]
        self.translated[ty] = ''
        self.double_translated[ty] = ''

        if "Краткое описание: " in text:
            text = text.split("Краткое описание: ")[1]

        # Split into parts of 1500 before translating
        text = [text[i:i + n] for i in range(0, len(text), n)]

        for part in text:

            eng_text = translate(part, 'en')
            deu_text = translate(eng_text, 'de')
            eng1_text = translate(deu_text, 'en')

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


def can_be_between(word):
    if len(word) == 2 and word.islower() and word not in PREPS or word[0].isupper() and len(word) == 1 or word == "-":
        return True
    return False


def can_be_big(word):
    if word[0].isupper() and word not in TITLES and word.upper() not in COUNTRIES and word.lower() not in PREPS:
        return True
    return False


def find_all_uppercase_sequences(w_list):
    seq = []
    words_list = w_list.copy()
    words_list = unite_countries_in(words_list)
    words_list = [words_list[i] for i in range(len(words_list)) if words_list[i] != '.' or len(words_list[i-1]) != 1]
    debug = False
    if debug:
        print(words_list)
    for i in range(len(words_list)):
        word = words_list[i]
        if can_be_big(word):
            try:
                n_word = words_list[i+1]
                words_list[i + 1] = ' '

                if can_be_big(n_word):
                    try:
                        nn_word = words_list[i+2]
                        words_list[i + 2] = ' '
                        if can_be_big(nn_word):
                            try:
                                nnn_word = words_list[i+3]
                                words_list[i + 3] = ' '
                                if can_be_big(nnn_word):
                                    fio = " ".join([word, n_word, nn_word, nnn_word])  # BBBB
                                    seq.append(fio)
                                else:
                                    fio = " ".join([word, n_word, nn_word])  # BBB
                                    seq.append(fio)
                            except IndexError:
                                fio = " ".join([word, n_word, nn_word])  # BBB
                                seq.append(fio)
                        elif can_be_between(nn_word):
                            try:
                                nnn_word = words_list[i + 3]
                                words_list[i + 3] = ' '
                                if can_be_big(nnn_word):
                                    fio = " ".join([word, n_word, nn_word, nnn_word])  # BBsB
                                    seq.append(fio)
                                else:
                                    fio = " ".join([word, n_word])  # BB
                                    seq.append(fio)
                            except IndexError:
                                fio = " ".join([word, n_word])  # BB
                                seq.append(fio)
                        else:
                            fio = " ".join([word, n_word])  # BB
                            seq.append(fio)
                    except IndexError:
                        fio = " ".join([word, n_word])  # BB
                        seq.append(fio)

                elif can_be_between(n_word):
                    try:
                        nn_word = words_list[i + 2]
                        words_list[i + 2] = ' '
                        if nn_word[0].isupper():
                            try:
                                nnn_word = words_list[i + 3]
                                words_list[i + 3] = ' '
                                if nnn_word[0].isupper():
                                    fio = " ".join([word, n_word, nn_word, nnn_word])  # BsBB
                                    seq.append(fio)
                                else:
                                    fio = " ".join([word, n_word, nn_word])  # BsB
                                    seq.append(fio)
                            except IndexError:
                                fio = " ".join([word, n_word, nn_word])  # BsB
                                seq.append(fio)
                        elif can_be_between(nn_word):
                            try:
                                nnn_word = words_list[i + 3]
                                words_list[i + 3] = ' '
                                if nnn_word[0].isupper():
                                    fio = " ".join([word, n_word, nn_word, nnn_word])  # BssB
                                    seq.append(fio)
                                else:
                                    fio = word  # B
                                    seq.append(fio)
                            except IndexError:
                                fio = word  # B
                                seq.append(fio)
                        else:
                            fio = word  # B
                            seq.append(fio)
                    except IndexError:
                        fio = word
                        seq.append(fio)
                else:
                    fio = word
                    seq.append(fio)
            except IndexError:
                fio = word
                seq.append(fio)

    to_remove = set()
    to_add = []

    # for s in seq:
    #     # if "." in s:
    #     #
    #     #     rem = s
    #     #     ad = s.split()
    #     #     point_idx = ad.index(".")
    #     #     ad = [a for a in ad if ad.index(a) != point_idx and ad.index(a) != point_idx-1]
    #     #     to_remove.add(rem)
    #     #     to_add.append(" ".join(ad))
    #     #
    #     # if "-" in s:
    #     #
    #     #     rem = s
    #     #     ad = s.split()
    #     #     point_idx = ad.index("-")
    #     #     ad = [a for a in ad if ad.index(a) != point_idx]
    #     #     to_remove.add(rem)
    #     #     to_add.append(" ".join(ad))
    #
    #     if s in STOP_WORDS:
    #         to_remove.add(s)

    seq = [s for s in seq if s not in to_remove]
    seq = [s for s in seq if s.lower() not in STOP_WORDS]

    for i in range(len(seq)):
        for w in seq[i].split():
            if len(w) == 1:
                seq[i] = seq[i].replace(w+' ', '')

    seq.extend(to_add)

    # seq = {' '.join(b) for a, b in itertools.groupby(words_list, key=lambda x: x[0].isupper() and x.lower() not in STOP_WORDS or len(x) <= 2 and x.islower() and words_list[words_list.index(x)+1][0].isupper() or x.isdigit()) if a}
    return seq


# def trim_words(text):
#     for k in range(3):
#         strings_to_check = {word if len(word) > 1 and not word.split()[0][0].islower() else " ".join(word.split()[1:]) for word in text}  # trim first words if lower
#         strings_to_check = {word if len(word) > 1 and not word.split()[-1][0].islower() else " ".join(word.split()[:-1]) for word in strings_to_check}  # trim last words if lower
#         strings_to_check = {word if word.lower() not in STOP_WORDS else "" for word in strings_to_check}  # delete stop words
#     strings_to_check = {word for word in strings_to_check if word}
#     return strings_to_check


STOP_PATH = './text_processing/stop-words.txt'
with open(STOP_PATH, "r") as f:
    STOP_WORDS = f.read().split('\n')

conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]
