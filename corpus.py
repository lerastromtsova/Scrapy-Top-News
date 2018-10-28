import sqlite3
from utils import count_countries, count_not_countries, iscountry, isfio
from utils import intersect, intersect_with_2_and_1, add_column
from document import Document
import operator


conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
all_rows = c.fetchall()
COUNTRIES = [row[0] for row in all_rows]


STOP_PATH_UNIQUE = 'text_processing/stop-words-unique.txt'
with open(STOP_PATH_UNIQUE, "r") as f:
    STOP_WORDS_UNIQUE = f.read().split('\n')
    # print(STOP_WORDS_UNIQUE)


class Topic:

    def __init__(self, name, init_news):

        self.name = name
        self.new_name = self.name.copy()

        self.new_name = {w for w in self.new_name if w.lower() not in STOP_WORDS_UNIQUE and not w.isdigit()}

        self.news = init_news
        # self.sentences_by_words = dict.fromkeys(self.name)

        self.main_words = set()
        self.unique_words = set()
        self.objects = set()
        self.obj = set()
        self.frequent = list()
        self.freq_dict = dict()
        self.method = set()
        self.subtopics = []
        self.methods_for_news = {}
        self.result = 0
        self.all_numbers = set()
        self.old_name = name.copy()

        self.sum_1 = 0
        self.sum_2 = 0
        self.prod = 0

        self.coefficient_sums = {}

        # for key in self.sentences_by_words:
        #     self.sentences_by_words[key] = []
        #
        # for word in self.name:
        #     for i, new in enumerate(self.news):
        #         for sent in new.sentences:
        #             if word in sent:
        #                 self.sentences_by_words[word].append(sent)

        # self.text_name = self.news[0].named_entities['content'].intersection(self.news[1].named_entities['content'])

    def all_words(self, text):
        return text, len(text)

    def all_wo_countries(self, text):
        all_wo_countries = [w for w in text if not iscountry(w)]
        return all_wo_countries, len(all_wo_countries)

    def all_wo_countries_and_small(self, text):
        all_wo_countries_and_small = [w for w in self.all_wo_countries(text)[0] if w[0].isupper()]
        return all_wo_countries_and_small, len(all_wo_countries_and_small)

    def fio(self, text):

        fio = [w for w in text if isfio(w)]
        return fio, len(fio)

    def big(self, text):
        big = [w for w in text if not iscountry(w) and w not in self.fio(text)[0] and w[0].isupper()]
        return big, len(big)

    def small(self, text):
        small = [w for w in text if w[0].islower()]
        return small, len(small)

    def countries(self, text):
        countries = [w for w in text if iscountry(w)]
        return countries, len(countries)

    def numbers(self, text):
        numbers = [w for w in text if all(char.isdigit() for char in w)]
        return numbers, len(numbers)

    def ids(self, text):
        ids = [w for w in text if any(char.isdigit() for char in w) and any(char.isalpha() for char in w)]

        return ids, len(ids)

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

        for i in range(1, len(self.news)):
            freq_words = intersect(freq_words, self.news[i].all_text)

        freq_words = {word for word in freq_words if word.upper() not in COUNTRIES}
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

    def frequent_50(self):
        token_freq = {}
        result = set()
        for new in self.news:
            for word in new.all_text:
                if word not in token_freq.keys():
                    token_freq[word] = 1
                else:
                    token_freq[word] += 1

        for k, i in token_freq.items():
            if i > len(self.news) / 2:
                result.add(k)
        result = {w for w in result if not any(w1 for w1 in result if w in w1 and w != w1)}
        return result


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

        try:
            self.create_documents(raw_data)

        except IndexError:
            self.create_columns_and_documents(raw_data)

    def create_documents(self, data):
        for i, row in enumerate(data):
            doc = Document(i, row, self.conn, self.table)
            self.data.append(doc)

    def create_columns_and_documents(self, raw_data):
        add_column(self.table, 'translated', 10000, self.c)
        add_column(self.table, 'translated1', 10000, self.c)
        add_column(self.table, 'translated_lead', 1000, self.c)
        add_column(self.table, 'translated1_lead', 1000, self.c)
        add_column(self.table, 'translated_title', 1000, self.c)
        add_column(self.table, 'translated1_title', 1000, self.c)
        add_column(self.table, 'nes_content', 1000, self.c)
        add_column(self.table, 'nes_lead', 1000, self.c)
        add_column(self.table, 'nes_title', 1000, self.c)
        add_column(self.table, 'tokens_content', 10000, self.c)
        add_column(self.table, 'tokens_lead', 1000, self.c)
        add_column(self.table, 'tokens_title', 1000, self.c)
        self.conn.commit()
        self.create_documents(raw_data)

    def find_topics(self, mode={"country":1, "not_country":2}):

        for row in self.data:
            others = [r for r in self.data if r.country != row.country]
            for ot in others:

                cw = intersect(row.all_text, ot.all_text)
                # cw = {w for w in cw if w[0].islower() or w in COUNTRIES}

                if count_not_countries(cw) >= mode["not_country"] and count_countries(cw) >= mode["country"]:
                    # if len(cw) >= 4 and count_countries(cw) >= 1:
                    news = [row, ot]
                    new_topic = Topic(cw, news)
                    self.topics.append(new_topic)

        self.topics = list(set(self.topics))

    def check_unique(self):
        ch = {"helicopter"}
        ch1 = {"Deir ez Zor"}
        other_topics = [t for t in self.topics]
        for topic in self.topics:

            for i, ot in enumerate(other_topics):

                if topic != ot:
                    if ot and topic:
                        if ot.name:

                            debug = False

                            cw = intersect_with_2_and_1(ot.name, topic.name)
                            if cw:
                                percent2 = len(cw) / len(topic.name)
                                countries_cw = count_countries(cw)
                                not_countries_cw = count_not_countries(cw)

                                # if (ch.issubset(topic.name) or ch1.issubset(topic.name)) and (ch.issubset(cw) or ch1.issubset(cw))  \
                                #     or (ch.issubset(ot.name) or ch1.issubset(ot.name)) and (ch.issubset(cw) or ch1.issubset(cw)):
                                #     debug = True

                                if countries_cw >= 1 and not_countries_cw >= 3 and len(topic.name) <= len(ot.name):
                                    if debug:
                                        print(f"Not deleting from {ot.name} because other topic is {topic.name}, "
                                              f"countries: {count_countries(cw)}, "
                                              f"not_countries: {count_not_countries(cw)},"
                                              f"common_words: {cw}")
                                    continue

                                elif countries_cw >= 1 and len(ot.name) < 3 and percent2 > 0.5:
                                    if debug:
                                        print(f"Not deleting from {ot.name} because other topic is {topic.name}, "
                                              f"countries: {count_countries(cw)}, "
                                              f"not_countries: {count_not_countries(topic.name)},"
                                              f"percent: {percent2},"
                                              f"common_words: {cw}")
                                    continue

                                elif countries_cw:
                                    # Удаляется слово, в котором присутствует любое слово из cw
                                    ot.new_name = {w for w in ot.new_name if
                                                      not any(c for r in cw for c in r.split() if r in w)}
                                    if debug:
                                        print(f"Deleting from {ot.name} because other topic is {topic.name},"
                                              f"1st topic is smaller than the 2nd, "
                                              f"common_words: {cw}"
                                              f"New name is: {ot.new_name}")

                                ot.new_name = {w for w in ot.new_name if w.lower() not in STOP_WORDS_UNIQUE and not w.isdigit()}

                                if not ot.new_name:
                                    other_topics[i] = None

        self.topics = [t for t in other_topics if t]

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