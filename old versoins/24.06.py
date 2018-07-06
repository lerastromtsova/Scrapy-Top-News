
from datetime import date

import sqlite3


from xl_stats import write_topics, write_news
from document import Document


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

        for key in self.sentences_by_words:
            self.sentences_by_words[key] = []

        for word in self.name:
            for i, new in enumerate(self.news):
                for sent in new.sentences:
                    if word in sent:
                        self.sentences_by_words[word].append(sent)



    def isvalid(self):

        a = self.point_a()
        c = self.point_c()
        d = self.point_d()

        self.valid = a | c | d
        return self.valid

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

        count_words = 0

        for word in self.name:
            all_sent = [set(s.split()) for s in self.sentences_by_words[word]]
            if all_sent:
                com_words = set.intersection(*all_sent)
                com_words -= {word}
                if com_words:
                    count_words += 1

                    self.main_words.update(com_words)

        if count_words >= 2:
            return True
        return False

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

        if count_not_countries(self.unique_words) >= 2 and count_countries(self.unique_words) >= 1:
            self.main_words.update(self.unique_words)
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
                # cw = {w.lower() for w in row1.description}.intersection({w1.lower() for w1 in row2.description})
                # cw = row1.named_entities['content'].intersection(row2.named_entities['content'])
                cw = row1.description.intersection(row2.description)
                # cw = {w for w in cw if w[0].islower() or w in COUNTRIES}
                if count_countries(cw) >= 1 and (count_countries(cw) >= 1 or row1.countries.intersection(row2.countries)):
                    self.frequencies[row1][row2] = len(cw)

    def find_topics(self):
        for row in self.data:
            others = [r for r in self.data if r.country != row.country]
            for ot in others:
                # cw = {w.lower() for w in row.description}.intersection({w1.lower() for w1 in ot.description})
                cw = row.description.intersection(ot.description)

                # cw = {w for w in cw if w[0].islower() or w in COUNTRIES}
                # cw = row.named_entities['content'].intersection(ot.named_entities['content'])
                if count_not_countries(cw) >= 2 and (count_countries(cw) >= 1 or row.countries.intersection(ot.countries)):
                    news = [row, ot]
                    new_topic = Topic(cw, news)
                    self.topics.append(new_topic)

        # for row1 in self.data:
        #     try:
        #         maxim = max(self.frequencies[row1].values())
        #         if maxim != 0:
        #             most_similar = {key: value for key, value in self.frequencies[row1].items() if value == maxim}
        #             for ms in most_similar:
        #                 if most_similar[ms][row1] == max(most_similar[ms].values()):
        #                     mss = {row1, ms}
        #                     name = {w.lower() for w in row1.description}.intersection({w1.lower() for w1 in ms.description})
        #
        #                     if mss not in self.similarities:
        #
        #                         self.similarities.append(mss)
        #                         new_topic = Topic(name, list(mss))
        #
        #                         self.topics.append(new_topic)
        #     except ValueError:
        #         continue

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
            if not topic.new_name:
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


def count_not_countries(name):
    countries = {w for w in name if w.upper() in COUNTRIES}
    not_countries = name - countries
    return len(not_countries)


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
    write_topics(f"1-{date.today().day}-{date.today().month}.xlsx", c.topics)
    c.delete_small()
    write_topics(f"2-{date.today().day}-{date.today().month}.xlsx", c.topics)
    # c.find_identic_topics()
    # write_topics(f"3-{date.today().day}-{date.today().month}.xlsx", c.topics)
    c.check_unique()
    write_topics(f"3-{date.today().day}-{date.today().month}.xlsx", c.topics)

    c.topics = [t for t in c.topics if t.isvalid()]
    write_topics(f"4-{date.today().day}-{date.today().month}.xlsx", c.topics)

    # c.find_unique()
    # write_topics(f"6-{date.today().day}-{date.today().month}.xlsx", c.trends)

    c.final_delete()
    write_topics(f"5-{date.today().day}-{date.today().month}.xlsx", c.topics)

    #
    # t = Tree(c)
    #
    # f = open("time1.txt", "w")
    # f.write(str(time.time()-now))