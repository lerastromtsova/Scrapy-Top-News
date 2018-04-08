"""
Here is where we double translate documents and save the output to DB
Input: db name
Output: tokens stored in db
"""
import sqlite3
from scrapnews.translate import translate
from scrapnews.preprocess import preprocess
import csv
from dates import process_dates
import nltk
from draw_graph import draw_graph
from numpy import median

LANGS = {'Germany': 'de',
         'Russia': 'ru',
         'United States': 'en',
         'United Kingdom': 'en'}


class Corpus:
    def __init__(self, db, table, with_uppercase):
        self.raw_data = []
        if isinstance(db, (list,)):
            for d in db:
                self.table = table
                self.conn = sqlite3.connect(f"db/{d}.db")
                self.c = self.conn.cursor()
                self.c.execute("SELECT * FROM " + table)
                self.raw_data.append(self.c.fetchall())  # a list of tuples [(country,title,content,url,time)]
        else:
            self.table = table
            self.conn = sqlite3.connect(f"db/{db}.db")
            self.c = self.conn.cursor()
            self.c.execute("SELECT * FROM " + table)
            self.raw_data.append(self.c.fetchall())  # a list of tuples [(country,title,content,url,time)]
        self.data = []  # data as it was extracted from DB
        self.tokens = []  # list of lists that represent tokenized sentences
        self.dict = set()  # dictionary of unique words
        self.translated = []  # list of 1st translated texts
        self.translated1 = []  # list of 2nd translated texts
        self.upper = with_uppercase
        self.dates = []
        self.named_entities = []

    def double_translate(self):
        n = 1500  # length limit

        for cor in self.raw_data:
            for row in cor:
                if not row[-1]:
                    country = row[0]
                    title = row[1]

                    if "Краткое описание: " in row[2]:
                        content = row[2].split("Краткое описание: ")[1]
                    else:
                        content = row[2]

                    if len(content) > n:
                        content = [content[i:i + n] for i in range(0, len(content), n)]
                    else:
                        content = [content]

                    eng_title = translate(title)
                    orig_title = translate(eng_title, language=LANGS[country])
                    eng1_title = translate(orig_title)

                    text = eng_title
                    text1 = eng1_title

                    for c in content:
                        eng_content = translate(c)
                        orig_content = translate(eng_content, language=LANGS[country])
                        eng1_content = translate(orig_content)

                        text += ' '
                        text += eng_content
                        text1 += ' '
                        text1 += eng1_content

                    self.translated.append(text)
                    self.translated1.append(text1)
                    self.update_db(row + (text, text1))
                else:
                    self.translated.append(row[-2])
                    self.translated1.append(row[-1])
                    self.data.append(row)

        self.conn.close()

    def find_common(self):
        for i in range(len(self.translated)):
            text = preprocess(self.translated[i], self.upper)
            text1 = preprocess(self.translated1[i], self.upper)
            common_words = []
            common_dict = set()
            for t in text:
                if t in text1:
                    common_words.append(t)
                    common_dict.add(t)
            self.tokens.append(common_words)
            for w in common_dict:
                self.dict.add(w)

            self.dates.append(process_dates(common_words))

    def update_db(self, row):
        url = row[3]
        self.c.execute(f"UPDATE {self.table} "
                       f"SET translated=?,translated1=?"
                       f" WHERE reference=?", (row[-2], row[-1], url))
        self.conn.commit()

    def find_frequencies(self, country):
        d = self.dict
        freq_all = {w: 0 for w in d}  # частота по всем
        freq_art = {w: 0 for w in d}  # частота по статьям
        if country != "All":
            for i, row in enumerate(self.data):
                if row[0] == country:
                    text = self.tokens[i]
                    for w in d:
                        c = text.count(w)
                        if c > 0:
                            freq_all[w] += c
                            freq_art[w] += 1
        else:
            for i, row in enumerate(self.data):
                text = self.tokens[i]
                for w in d:
                    c = text.count(w)
                    if c > 0:
                        freq_all[w] += c
                        freq_art[w] += 1

        return freq_all, freq_art

    def extract_entities(self):
        for text in self.tokens:
            nes = []
            parse_tree = nltk.ne_chunk(nltk.tag.pos_tag(text), binary=True)  # POS tagging before chunking!
            for t in parse_tree.subtrees():
                if t.label() == 'NE':
                    nes.append(list(t))
            self.named_entities.append(nes)


def build_stats(db):
    corpus = Corpus(db, 'buffer', with_uppercase=False)
    corpus.double_translate()
    corpus.find_common()
    frequency_all = {}
    frequency_art = {}
    for country in LANGS.keys():
        frequency_all[country], frequency_art[country] = corpus.find_frequencies(country)
    if isinstance(db, (list,)):
        file = csv.writer(open(f"test.csv", "w"))
    else:
        file = csv.writer(open(f"test{db}.csv", "w"))
    headers = ['Word', 'All content', 'All articles', 'Articles in RF', 'All in RF', 'Articles in USA', 'All in USA',
               'Articles in GB', 'All in GB', 'Articles in FRG', 'All in FRG','In which countries','In how many countries']
    file.writerow(headers)

    for word in corpus.dict:
        f_all_c = 0
        f_art_c = 0
        by_country = []
        for country in LANGS.keys():
            f_all_c += frequency_all[country][word]
            f_art_c += frequency_art[country][word]
            if frequency_all[country][word]>0:
                by_country.append(country)
        file.writerow([word,f_all_c,f_art_c,frequency_art['Russia'][word],frequency_all['Russia'][word],
                       frequency_art['United States'][word],frequency_all['United States'][word],
                       frequency_art['United Kingdom'][word], frequency_all['United Kingdom'][word],
                       frequency_art['Germany'][word], frequency_all['Germany'][word],
                       by_country, len(by_country)])

# build_stats('day')
# build_stats('week')
# build_stats('month')
# build_stats('mydatabase-2')
# build_stats(['day','week','month','mydatabase-2'])

def stats_by_articles(db):
    corpus = Corpus(db, 'buffer', with_uppercase=True)
    corpus.double_translate()
    corpus.find_common()
    corpus.extract_entities()

    file = csv.writer(open(f"articles{db}.csv", "w"))
    headers = ['Article','Title (original)', 'Text (original)', 'Title + Text (En)', 'Common words',
               'Uppercase letter', 'Dates', 'Entities (with NLTK library)']
    file.writerow(headers)

    for i,row in enumerate(corpus.data):
        file.writerow([row[3], row[1], row[2], corpus.translated1[i], corpus.tokens[i],
                       [c for c in corpus.tokens[i] if c[0].isupper()],
                       corpus.dates[i],corpus.named_entities[i]])


def visualize(db,m,uppercase=False,dates=False,nes=False):
    corpus = Corpus(db, 'buffer', with_uppercase=True)
    corpus.double_translate()
    corpus.find_common()
    corpus.extract_entities()

    edges = []

    for i in range(len(corpus.data)):
        for j in range(i+1,len(corpus.data)):
                weight = 0

                if uppercase:

                    u = [c for c in corpus.tokens[i] if c[0].isupper()]
                    u1 = [c for c in corpus.tokens[j] if c[0].isupper()]
                    common_upper = [w for w in u if w in u1]
                    weight += len(common_upper)

                if dates:

                    d = corpus.dates[i]
                    d1 = corpus.dates[j]
                    common_dates = [w for w in d if w in d1]
                    weight += len(common_dates)

                if nes:

                    ne = corpus.named_entities[i]
                    ne1 = corpus.named_entities[j]
                    common_nes = [w for w in ne if w in ne1]
                    weight += len(common_nes)

                if weight>m:

                    edges.append((i,j,weight))


    nodes = [{'title': corpus.translated[i], 'url': row[3], 'country': row[0]} for i,row in enumerate(corpus.data)]

    fname = ''
    if uppercase:
        fname += 'F '
    if dates:
        fname += 'G '
    if nes:
        fname += 'H '

    draw_graph(nodes,edges,m=m,fname=fname, type="без связей внутри")


visualize('day',m=20,uppercase=True)
visualize('day',m=20,nes=True)