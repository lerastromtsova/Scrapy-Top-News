
from datetime import date

import sqlite3

from xl_stats import write_topics, write_news
from document import Document
import operator


conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]


class Topic:

    def __init__(self, name, init_news):

        self.name = name
        self.new_name = self.name.copy()

        self.news = init_news
        self.sentences_by_words = dict.fromkeys(self.name)

        self.main_words = set()
        self.unique_words = set()
        self.objects = set()
        self.obj = set()
        self.frequent = []

        self.method = set()

        self.subtopics = set()

        for key in self.sentences_by_words:
            self.sentences_by_words[key] = []

        for word in self.name:
            for i, new in enumerate(self.news):
                for sent in new.sentences:
                    if word in sent:
                        self.sentences_by_words[word].append(sent)

        self.text_name = self.news[0].named_entities['content'].intersection(self.news[1].named_entities['content'])
        self.freq_dict = {}


    def isvalid(self):

        a = self.point_a()
        b = self.point_b()
        c = self.point_c()
        d = self.point_d()
        e = self.point_e()
        f = self.point_f()
        self.valid = a | c | d

        if a:
            self.method.add("a")
        if c:
            self.method.add("c")
        if d:
            self.method.add("d")

        if e:
            self.method.add("e")
            return self.valid

        return self.valid & f

    def point_a(self):

        # Пункт а
        # С названиями

        com_words = self.news[0].descr_with_countries.intersection(self.news[1].descr_with_countries)

        # com_words = self.news[0].description.intersection(self.news[1].description)

        if count_countries(com_words) >= 1 and count_not_countries(com_words) >= 2:

            self.main_words.update(com_words)
            return True
        return False

    def point_b(self):

        # Пункт б
        # Вариант "Или"

        sents = [{s: {w for w in self.new_name if w in s} for s in new.sentences} for new in self.news]
        a = False
        b = False


        for new in sents:
            other = [s for s in sents if s != new]
            for o in other:
                if any([len(val1.intersection(val2)) >= 2 for val1 in new.values() for val2 in o.values()]):
                    a = True

        for new in sents:
            other = [s for s in sents if s != new]
            for o in other:
                if any([len(set(s1.split()).intersection(set(s2.split()))-self.unique_words) >= 2 and len(v1) >= 2 and len(v2) >= 2 for s1,v1 in new.items() for s2,v2 in o.items()]):
                    b = True

        return a | b

    def point_c(self):

        # Пункт в

        for new in self.news:
            cw_in_tokens = new.descr_with_countries.intersection(self.new_name)

            if count_countries(cw_in_tokens) >= 1 and count_not_countries(cw_in_tokens) >= 2:
                    # count_countries(cw_in_tokens) >= 2 and count_not_countries(cw_in_tokens) >= 1:

                self.main_words.update(cw_in_tokens)
                return True
        return False

    def point_d(self):

        # un_words = {w for w in self.new_name if w[0].islower()}
        # if len(un_words) >= 2:

        if count_not_countries(self.new_name) >= 2 and count_countries(self.new_name) >= 1:
            self.main_words.update(self.new_name)
            return True
        return False

    def point_e(self):

        # un_words = {w for w in self.new_name if w[0].islower()}
        # if len(un_words) >= 2:
        text = set.intersection(*[n.named_entities['content'] for n in self.news])

        if count_not_countries(self.new_name) >= 3 and count_countries(text) >= 1:
            self.main_words.update(self.new_name)
            return True
        return False

    def point_f(self):
        text = set.intersection(*[n.named_entities['content'] for n in self.news])
        if count_not_countries(text) < 2:
            return False
        else:
            return True

    def most_frequent(self):
        freq_words = set(self.news[0].all_text)
        for i in range(1,len(self.news)):
            freq_words = intersect(freq_words, self.news[i].all_text)
        freq_words = {word for word in freq_words if word not in COUNTRIES}
        freq_dict = dict.fromkeys(freq_words, 0)

        for word in freq_words:
            for new in self.news:
                all_text = new.translated['title'] + new.translated['lead'] + new.translated['content']
                all_text = all_text.lower()
                c = all_text.count(word.lower())
                freq_dict[word] += c

        for word, c in freq_dict.items():
            for ent in self.name:
                if word in ent and len(ent) > len(word):
                    try:
                        freq_dict[ent] += freq_dict[word]
                        freq_dict[word] = 0
                    except KeyError:
                        try:
                            freq_dict[ent] = freq_dict[word]
                            del freq_dict[word]
                        except KeyError:
                            continue

        ans = sorted(freq_dict.items(), key=operator.itemgetter(1), reverse=True)
        ans = [a[0] for a in ans if a[1] != 0]

        self.frequent = ans

        return ans

class CorpusD:

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


    def find_topics(self):

        for row in self.data:
            others = [r for r in self.data if r.country != row.country]
            for ot in others:

                cw = intersect(row.description, ot.description)
                cw = {w for w in cw if w[0].islower() or w in COUNTRIES}

                if count_not_countries(cw) >= 2 and (count_countries(cw) >= 1 or row.countries.intersection(ot.countries)):
                    news = [row, ot]
                    new_topic = Topic(cw, news)
                    self.topics.append(new_topic)

        self.topics = list(set(self.topics))

    def check_unique(self):
        for topic in self.topics:
            other_topics = [t for t in self.topics if t != topic]
            for ot in other_topics:
                cw = topic.name.intersection(ot.name)
                percent1 = len(cw) / len(topic.name)
                percent2 = len(cw) / len(ot.name)

                if count_countries(cw) >= 1 and percent1 >= 0.5 and percent2 >= 0.5:
                    continue
                else:
                    topic.new_name -= cw

        to_remove = set()
        for topic in self.topics:
            if not topic.new_name:
                to_remove.add(topic)

        self.topics = [t for t in self.topics if t not in to_remove]

    def delete_small(self):
        all_names = {frozenset(topic.name) for topic in self.topics}
        self.topics.sort(key=lambda t: -len(t.name))
        to_remove = set()
        to_add = set()

        for topic in self.topics:
            if any(topic.name.issubset(other) for other in all_names if topic.name != other):
                to_remove.add(topic)

        for topic in self.topics:
            others = [t for t in self.topics if t != topic]
            for other in others:
                if topic.name == other.name and set(topic.news) == set(other.news):
                    to_remove.add(topic)
                    to_remove.add(other)
                    if other not in to_add:
                        to_add.add(topic)

        self.topics = [t for t in self.topics if t not in to_remove]
        self.topics.extend(to_add)

    def find_unique(self):

        self.trends = []

        all_names = {frozenset(topic.name) for topic in self.topics}
        for t in self.topics:

            unique_words = t.name.copy()

            for key in all_names:
                if not t.name.issubset(key):
                    unique_words -= key

            if unique_words:
                t.main_words = unique_words
                self.trends.append(t)

    def final_delete(self):
        to_remove = set()
        for topic in self.topics:
            text = set.intersection(*[n.named_entities['content'] for n in topic.news])
            if count_not_countries(text) < 2:
                to_remove.add(topic)
        self.topics = [t for t in self.topics if t not in to_remove]


def count_countries(name):
    countries = {w for w in name if w.upper() in COUNTRIES}
    return len(countries)

def iscountry(str):
    if str in COUNTRIES:
        return True
    return False


def count_not_countries(name):
    countries = {w for w in name if w.upper() in COUNTRIES}
    not_countries = name - countries
    return len(not_countries)

def intersect(set1,set2):
    new1 = set1.copy()
    new2 = set2.copy()
    for s1 in set1:
        for s2 in set2:
            if s2 == s1+'s' or s2 == s1+'es' or s2 == s1+'ies':
                new2.remove(s2)
                new2.add(s1)
    return new1.intersection(new2)
# if __name__ == '__main__':
#
#     db = input("DB name (default - day): ")
#     table = input("Table name (default - buffer): ")
#
#     if not db:
#         db = "day"
#     if not table:
#         table = "buffer"
#
#     c = Corpus(db, table)
#
#     c.find_topics()
#     write_topics(f"1-{date.today().day}-{date.today().month}.xlsx", c.topics)
#
#     c.delete_small()
#     write_topics(f"2-{date.today().day}-{date.today().month}.xlsx", c.topics)
#
#     c.check_unique()
#     write_topics(f"3-{date.today().day}-{date.today().month}.xlsx", c.topics)
#
#     c.topics = [t for t in c.topics if t.isvalid()]
#     write_topics(f"4-{date.today().day}-{date.today().month}.xlsx", c.topics)
#
#     c.final_delete()
#     write_topics(f"5-{date.today().day}-{date.today().month}.xlsx", c.topics)