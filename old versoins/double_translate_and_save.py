"""
Here is where we double translate documents and save the output to DB
Input: db name
Output: tokens stored in db
"""
from text_processing.translate import translate
from text_processing.preprocess import preprocess
from text_processing.dates import process_dates
# from draw_graph import draw_graph

import sqlite3
import csv
import nltk
import pandas as pd

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
                    for k in list(t):
                        nes.append(k[0])
            self.named_entities.append(set(nes))


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
                       set([c for c in corpus.tokens[i] if c[0].isupper()]),
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
                    common_upper = set([w for w in u if w in u1])
                    weight += len(common_upper)

                if dates:

                    d = corpus.dates[i]
                    d1 = corpus.dates[j]
                    common_dates = set()
                    for w in d:
                        for w1 in d1:
                            if w[0] == w1[0] and w[1] == w1[1] and w[0] != 'None' and w[1] != 'None':
                                common_dates.add(w)
                    weight += len(common_dates)

                if nes:

                    ne = corpus.named_entities[i]
                    ne1 = corpus.named_entities[j]
                    print(ne1)
                    print(ne)
                    common_nes = set([w for w in ne if w in ne1])
                    weight += len(common_nes)

                if weight>m:

                    edges.append((i,j,weight))
    dates = []
    for i in range(len(corpus.dates)):
        print(corpus.dates[i])
        dates.append([f"{date[0]}.{date[1]}.{date[2]};" for date in corpus.dates[i]])
    nodes = [{'title': corpus.translated[i][:100], 'url': row[3], 'country': row[0], 'date': ' '.join(dates[i])} for i,row in enumerate(corpus.data)]

    fname = ''
    if uppercase:
        fname += 'F '
    if dates:
        fname += 'G '
    if nes:
        fname += 'H '

    # draw_graph(nodes,edges,m=m,fname=fname, type="без связей внутри")


# visualize('day',m=3,uppercase=True)
# visualize('day',m=0,dates=True)

def find_main_topics(dframe):

    main_topics = {}
    mains = []

    for i in range(dframe.shape[0]):
        ma = 0
        for j in range(dframe.shape[1]):
            if type(dframe.ix[i][j]) == set:
                if len(dframe.ix[i][j])>ma:
                    ma = len(dframe.ix[i][j])
                    main_idx = j
        if main_idx:
            mains.append(main_idx)

    return mains


def create_df(named_entities):

    df = pd.DataFrame(index=[i for i in range(len(named_entities))], columns=[i for i in range(len(named_entities))])
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            if i != j:
                df.ix[i][j] = named_entities[i].intersection(named_entities[j])

    return df

def find_main_for_it(dframe,mains):

    cols = set(range(dframe.shape[0]))-set(mains)
    main_df = pd.DataFrame(index=mains,columns=cols,data=[[dframe[i][j] for j in cols] for i in mains])
    main_for_each = {}

    for j in cols:
        sublist = [len(item) if type(item) == set else 0 for item in main_df.loc[:,j]]
        main_for_it = sublist.index(max(sublist))
        main_for_each[j] = list(main_df.index.values)[main_for_it]


    return main_for_each, main_df


corpus = Corpus('day', 'buffer', with_uppercase=True)
corpus.double_translate()

corpus.find_common()

corpus.extract_entities()

news_df = create_df(corpus.named_entities)

main_topics = find_main_topics(news_df)
main_for_each, main_df = find_main_for_it(news_df, main_topics)

not_main = set(range(news_df.shape[0])) - set(main_topics)
m_for_each = {}
print(main_for_each)
rest_words = {}

f = open("news.csv", "w")
file = csv.writer(f, delimiter=',')
headers = ['Main','Entities in main','# of articles in topic','Articles','Common words']
file.writerow(headers)
for i in set(main_for_each.values()):
    print(i)
    main = corpus.translated[i]
    ents_in_main = corpus.named_entities[i]
    art_index = [key for key,val in main_for_each.items() if val==i]
    num_articles = len(art_index)
    row = [main,ents_in_main,num_articles]

    articles = [(corpus.translated[ind],corpus.named_entities[ind].intersection(ents_in_main)) for ind in art_index]

    for art in articles:
        row.append(art[0])
        row.append(art[1])

    file.writerow(row)
    f.flush()

f.close()


print("Written rows")

for j in not_main:

    com_words = news_df.iloc[main_for_each[j]][j]
    t = news_df
    if type(com_words) != float:
        nes = [row if i != j else corpus.named_entities[j]-com_words for i,row in enumerate(corpus.named_entities)]
        rest_words[j] = corpus.named_entities[j]-com_words
        new_df = create_df(nes)
        # news_df.iloc[main_for_each[j]][j] = corpus.named_entities[j]-com_words
        new_main_for_each, main_df = find_main_for_it(new_df,main_topics)
        m_for_each[j] = new_main_for_each[j]
        # news_df.iloc[main_for_each[j]][j] = com_words
        nes = corpus.named_entities

print(m_for_each)

# file = csv.writer(open("news.csv", "w"))
# headers = ['News','Entities','Common words-1','Main-1','Words in main 1','CW1','Common words-2','Main-2','Words in main 2']
# file.writerow(headers)
# for i in not_main:
#     news = corpus.translated[i]
#
#     entities = corpus.named_entities[i]
#     common_words1 = news_df[main_for_each[i]][i]
#     main1 = corpus.translated[main_for_each[i]]
#     e1 = corpus.named_entities[main_for_each[i]]
#
#     common_words2 = news_df[m_for_each[i]][i]
#     main2 = corpus.translated[m_for_each[i]]
#     e2 = corpus.named_entities[m_for_each[i]]
#     cw1 = rest_words[j].intersection(e2)
#     file.writerow([news,entities,common_words1,main1,e1,cw1,common_words2,main2,e2])


f = open("news1.csv", "w")
file = csv.writer(f,delimiter=',')
headers = ['Main','Entities in main','# of articles in topic','Articles','Common words']
file.writerow(headers)

for i in set(m_for_each.values()):
    main = corpus.translated[i]
    ents_in_main = corpus.named_entities[i]
    art_index = [key for key, val in m_for_each.items() if val == i]
    num_articles = len(art_index)
    row = [main, ents_in_main, num_articles]

    articles = [(corpus.translated[ind], corpus.named_entities[ind].intersection(ents_in_main)) for ind in art_index]

    for art in articles:
        row.append(art[0])
        row.append(art[1])

    file.writerow(row)
    f.flush()

f.close()
