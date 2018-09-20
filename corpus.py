import sqlite3

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
        # self.sentences_by_words = dict.fromkeys(self.name)

        self.main_words = set()
        self.unique_words = set()
        self.objects = set()
        self.obj = set()
        self.frequent = list()
        self.freq_dict = dict()
        self.method = set()
        self.subtopics = set()
        self.methods_for_news = {}
        self.result = 0
        self.all_numbers = set()
        self.old_name = name.copy()

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
        all_wo_countries = [w for w in text if w not in COUNTRIES]
        return all_wo_countries, len(all_wo_countries)

    def all_wo_countries_and_small(self, text):
        all_wo_countries_and_small = [w for w in self.all_wo_countries(text)[0] if w[0].isupper()]
        return all_wo_countries_and_small, len(all_wo_countries_and_small)

    def fio(self, text):
        fio = [w for w in text if ' ' in w and w not in COUNTRIES]
        return fio, len(fio)

    def big(self, text):
        big = [w for w in text if w not in COUNTRIES and w not in self.fio(text)[0] and w[0].isupper()]
        return big, len(big)

    def small(self, text):
        small = [w for w in text if w[0].islower()]
        return small, len(small)

    def countries(self, text):
        countries = [w for w in text if w in COUNTRIES]
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

    def find_topics(self):

        for row in self.data:
            others = [r for r in self.data if r.country != row.country]
            for ot in others:

                cw = intersect(row.all_text, ot.all_text)
                # cw = {w for w in cw if w[0].islower() or w in COUNTRIES}

                # if count_not_countries(cw) >= 2 and (count_countries(cw) >= 1 or row.countries.intersection(ot.countries)):
                if len(cw) >= 4 and count_countries(cw) >= 1:
                    news = [row, ot]
                    new_topic = Topic(cw, news)
                    self.topics.append(new_topic)

        self.topics = list(set(self.topics))

    def check_unique(self):
        ch = {"Salisbury", "RUSSIA", "UNITED KINGDOM", "Alexander Litvinenko"}
        for topic in self.topics:
            other_topics = [t for t in self.topics if t != topic]
            # not_similar_topic_names = [word for t in other_topics for word in t.name if len(intersect_with_two(topic.name, t.name))/len(t.name) <= 0.5]

            # print("Do imya temy", topic.name)
            # for word in topic.name:
            #     max_freq_word = ''
            #     word_list = word.split()
            #     if len(word_list) >= 3:
            #         freqs = [not_similar_topic_names.count(w) for w in word_list]
            #         max_freq_idx = freqs.index(max(freqs))
            #         max_freq_word = word_list[max_freq_idx]
            #     print("Do slovo ", word)
            #     topic.name -= {word}
            #     word = ' '.join([w for w in word_list if w != max_freq_word])
            #     topic.name.add(word)
            #     print("Posle slovo ", word)
            # print("Posle imya temy", topic.name)

            for ot in other_topics:
                # cw = topic.name.intersection(ot.name)
                # percent1 = len(cw) / len(topic.name)
                if ot.name:

                    debug = False

                    if ch.issubset(topic.name) or ch.issubset(ot.name):
                        debug = True

                    cw = intersect_with_2_and_1(topic.name, ot.name)
                    percent2 = len(cw) / len(ot.name)

                    if percent2 > 0.5:
                        continue

                    elif count_countries(cw):

                        topic.new_name = {w for w in topic.new_name if not any(c for r in cw for c in r.split() if r in w)}
                        if debug:
                            print("1st topic", topic.name)
                            print("2nd topic", ot.name)
                            print("Common", cw)
                            print(topic.new_name)

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


def iscountry(str):
    if str in COUNTRIES:
        return True
    return False


def count_countries(name):
    countries = {w for w in name if iscountry(w)}
    return len(countries)


def count_not_countries(name):
    not_countries = {w for w in name if not iscountry(w)}
    return len(not_countries)


def intersect_with_two(set1, set2):
    new1 = set1.copy()
    new2 = set2.copy()
    for s1 in set1:
        for s2 in set2:
            words_1 = set(s1.split())
            words_2 = set(s2.split())
            if len(words_1) >= 2:
                if len(words_2) >= 2:
                    cw = words_1.intersection(words_2)
                    if len(cw) >= 2:
                        if len(words_1) > len(words_2):
                            if s1 in new1:
                                new1.remove(s1)
                                # print("removed: ", s1)
                                new1.add(s2)
                                # print("added: ", s2)
                        else:
                            if s2 in new2:
                                new2.remove(s2)
                                # print("removed: ", s2)
                                new2.add(s1)
                                # print("added: ", s1)
    return new1.intersection(new2)

def intersect_with_2_and_1(set1, set2):
    new1 = set1.copy()
    new2 = set2.copy()
    for s1 in set1:
        for s2 in set2:
            words_1 = set(s1.split())
            words_2 = set(s2.split())
            if len(words_1) >= 2:
                if len(words_2) >= 2:
                    cw = words_1.intersection(words_2)
                    if len(cw) >= 2:
                        if len(words_1) > len(words_2):
                            if s1 in new1:
                                new1.remove(s1)
                                new1.add(s2)
                        else:
                            if s2 in new2:
                                new2.remove(s2)
                                new2.add(s1)
                if len(words_2) == 1:
                    cw = words_1.intersection(words_2)
                    if cw:
                        new1.remove(s1)
                        new1.add(s2)
            if len(words_1) == 1:
                if len(words_2) >= 2:
                    cw = words_1.intersection(words_2)
                    if cw:
                        new2.remove(s2)
                        new2.add(s1)
    return new1.intersection(new2)

def intersect(set1, set2):
    new1 = set1.copy()
    new2 = set2.copy()
    for s1 in set1:
        for s2 in set2:
            if s2.lower() == s1.lower()+'s' or s2.lower() == s1.lower()+'es' or s2.lower() == s1.lower()+'ies':
                if s2 in new2:
                    new2.remove(s2)
                new2.add(s1)
            elif s1.lower() == s2.lower()+'s' or s1.lower() == s2.lower()+'es' or s1.lower() == s2.lower()+'ies':
                if s1 in new1:
                    new1.remove(s1)
                new1.add(s2)
            elif s1.lower() == s2:
                if s1 in new1:
                    new1.remove(s1)
                new1.add(s2)
            elif s1 == s2.lower():
                if s2 in new2:
                    new2.remove(s2)
                new2.add(s1)
    return new1.intersection(new2)

def add_column(table, column_name, length, cursor):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} TEXT({length})")
    except sqlite3.OperationalError:
        pass
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