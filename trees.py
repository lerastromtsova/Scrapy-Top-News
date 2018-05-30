import re
import time
import operator

import nltk
import sqlite3
import csv

from text_processing.preprocess import preprocess
from text_processing.translate import translate
from text_processing.dates import process_dates


class Corpus:

    def __init__(self, db, table, with_lead=False, analyze=('content',)):

        self.table = table
        self.conn = sqlite3.connect(f"db/{db}.db")
        self.c = self.conn.cursor()
        self.c.execute("SELECT * FROM " + table)
        self.topics = []
        self.data = []

        raw_data = self.c.fetchall()

        for row in raw_data:
            self.data.append(Document(row, self.conn, table, with_lead, analyze))

    def find_topics(self):

        for row1 in self.data:
            rows_except_this = [r for r in self.data if r.url != row1.url and r.country != row1.country]
            for row2 in rows_except_this:
                com_words = row1.named_entities.intersection(row2.named_entities)
                if len(com_words) and com_words not in self.topics:
                    self.topics.append(com_words)

        self.topics.sort(key=lambda s: -len(s))


class Document:

    def __init__(self, row, conn, table, with_lead=False, analyze=('title', 'lead', 'content')):

        self.country = row[0]
        self.title = row[1]
        self.content = ''
        self.translated = ''
        self.double_translated = ''

        if with_lead:
            self.lead = row[2]
            if 'title' in analyze:
                self.content += self.title
                if row[9]:  # if title is already translated
                    self.translated += row[9]
                else:
                    self.double_translate(type='title')
            if 'lead' in analyze:
                self.content += ' '
                self.content += self.lead
                if row[11]:  # if lead is already translated
                    self.translated += row[11]
                else:
                    self.double_translate(type='lead')
            if 'content' in analyze:
                self.content += ' '
                self.content += row[3]
                if row[6]:  # if content is already translated
                    self.translated += row[6]
                else:
                    self.double_translate(type='content')
            self.url = row[4]
            self.date = row[5]
            self.translated = row[6]
            self.double_translated = row[7]

        else:
            if 'title' in analyze:
                self.content = self.title
                if row[8]:  # if title is already translated
                    self.translated += row[8]
                else:
                    self.double_translate(type='title')
            if 'content' in analyze:
                self.content += ' '
                self.content += row[2]
                if row[5]:  # if content is already translated
                    self.translated += row[5]
                else:
                    self.double_translate(type='content')
            self.content = row[2]
            self.url = row[3]
            self.date = row[4]
            self.translated = row[5]
            self.double_translated = row[6]

        self.tokens = []
        self.removed_words = []
        self.start_words = {}
        self.conn = conn
        self.table = table

        for tr in preprocess(self.translated):
            if tr in preprocess(self.double_translated):
                self.tokens.append(tr)

        # self.named_entities = {word for word in self.tokens if word[0].isupper()}

        parse_tree = nltk.ne_chunk(nltk.tag.pos_tag(self.tokens), binary=True)  # POS tagging before chunking!
        self.named_entities = {k[0] for t in parse_tree.subtrees() for k in list(t) if t.label() == 'NE'}

        c = self.conn.cursor()
        c.execute(f"UPDATE {self.table} SET named_entities=(?) WHERE reference=(?)",
                      (' '.join(self.named_entities), self.url))
        self.conn.commit()

        self.unite_countries()
        self.find_entities()
        self.unite_countries()

        self.dates = process_dates(list(self.tokens)).append(self.date)

    def find_entities(self):

        text = re.findall(r"[\w]+|[^\s\w]", self.translated)
        to_remove = set()
        to_add = set()

        for ent1 in self.named_entities:
            if ent1 in text:
                idx1 = text.index(ent1)
                entities_except_this = self.named_entities - set(ent1)

                for ent2 in entities_except_this:
                    if ent2 in text:
                        idx2 = text.index(ent2)
                        if ((idx2 - idx1 == 2) and (text[idx1+1] == ' ' or text[idx1+1] == '-'
                                                    or text[idx1+1] == "'" or text[idx1+1] == 'of')) or idx2 - idx1 == 1:

                            united_entity = ' '.join([ent1,ent2])
                            to_add.add(united_entity)
                            to_remove.add(ent1)
                            to_remove.add(ent2)

        self.named_entities = (self.named_entities - to_remove) | to_add  # Because we cannot change set while iterating

    def unite_countries(self):

        conn = sqlite3.connect("db/countries.db")
        c = conn.cursor()
        c.execute("SELECT * FROM countries")
        all_rows = c.fetchall()
        to_remove = set()
        to_add = set()

        for ent in self.named_entities:
            for row in all_rows:
                low = [w.lower() for w in row if w is not None]
                if ent.lower() in low:
                    to_remove.add(ent)
                    to_add.add(row[0])

        self.named_entities = (self.named_entities - to_remove) | to_add

    def double_translate(self, type):

        n = 1500  # length limit
        if type == "title":
            text = self.title
        if type == "lead":
            text = self.lead
        if type == "content":
            text = self.content

        if "Краткое описание: " in text:
            text = text.split("Краткое описание: ")[1]

        # Split into parts of 1500 before translating
        text = [text[i:i + n] for i in range(0, len(text), n)]

        for t in text:

            eng_text = translate(t)
            orig_text = translate(eng_text, self.country)
            eng1_text = translate(orig_text)

            self.translated += ' '.join([self.translated, eng_text])
            self.double_translated += ' '.join([self.double_translated, eng1_text])

        c = self.conn.cursor()
        c.execute(f"UPDATE {self.table} SET translated=(?), translated1=(?) WHERE reference=(?)",
                  (self.translated, self.double_translated, self.url))
        self.conn.commit()


class Node:

    def __init__(self, item):

        self.name = item
        self.level = len(self.name)

        self.parents = []
        self.children = []
        self.documents = []
        self.percents = []
        self.subtopics = []

    def has_free_links(self, other_node):

        topic = self.name
        my_free_words = [d.named_entities - topic for d in self.documents]
        suit_documents = [sd for sd in self.documents if sd not in other_node.documents]
        par_free_words = [pd.named_entities - topic for pd in suit_documents]
        connection = 0

        for doc in my_free_words:
            for d in par_free_words:
                if doc.intersection(d):
                    connection+=1

        if my_free_words and par_free_words:
            percent_of_connected = connection/(len(my_free_words)*len(par_free_words))
            return percent_of_connected
        return 0

    def add_document(self,doc):
        self.documents.append(doc)

    def assign_parent(self,parent):
        if parent not in self.parents:
            self.parents.append(parent)
            self.percents.append(self.has_free_links(parent))

    def assign_child(self,child):
        if child not in self.children:
            self.children.append(child)

    def isparent(self,other_node):
        if other_node in self.parents:
            return True
        return False

    def ischild(self,other_node):
        if other_node in self.children:
            return True
        return False

    def isroot(self):
        if self.parents:
            return False
        return True

    def isleaf(self):
        if self.children:
            return False
        return True

    def contains(self, children):
        for ch in children:
            if self.name.issubset(ch.name):
                return True
        return False


class Tree:

    def __init__(self,corpus):

        self.nodes = [Node(item) for item in corpus.topics]
        self.assign_documents(corpus)

        for node in self.nodes:

            for other_node in [n for n in self.nodes if n!=node]:

                if node.name.issubset(other_node.name) and node not in other_node.children and not node.contains(other_node.children):
                    node.assign_parent(other_node)
                    other_node.assign_child(node)

                if other_node.name.issubset(node.name) and node not in other_node.parents and not other_node.contains(node.children):
                    other_node.assign_parent(node)
                    node.assign_child(other_node)

        self.roots = [n for n in self.nodes if n.isroot()]
        write_topics_to_xl("корневые темы.csv",self.roots)
        self.last_nodes = set()

    def assign_documents(self,corpus):

        for node in self.nodes:
            for doc in corpus.data:
                if node.name.issubset(doc.named_entities):
                    node.add_document(doc)

    def find_last_topics(self):
        for root in self.roots:
            x = check_free([root])
            if x:
                self.last_nodes.add(x)
        write_topics_to_xl("после обрезания.csv", self.last_nodes)

    def unite_similar_topics(self):
        to_remove = set()

        for n in self.last_nodes:
            other_nodes = self.last_nodes - {n}
            for on in other_nodes:
                if n.name.issubset(on.name):
                    to_remove.add(n)

        self.last_nodes -= to_remove
        write_topics_to_xl("удалили дубликаты.csv", self.last_nodes)

        tr_1, ta_1 = self.add_and_remove(principle="country")
        self.last_nodes = (self.last_nodes-tr_1)|ta_1
        write_topics_to_xl("после объединения.csv", self.last_nodes, with_children=True)



        #nodes = sorted(list(self.last_nodes), key=lambda n: len(n.name))
        # old_nodes = self.last_nodes
        #
        # while old_nodes:
        #     to_remove = set()
        #     to_add = set()
        #
        #     for node in self.last_nodes:
        #         other_nodes = self.last_nodes-{node}
        #
        #         for other_node in other_nodes:
        #             if all(elem in node.documents for elem in other_node.documents):  #node contains all of other_node
        #                 new_node = Node(node.name | other_node.name)
        #                 new_node.subtopics = [node, other_node]
        #                 new_node.documents = node.documents
        #                 old_nodes.remove(node)
        #                 old_nodes.remove(other_node)
        #                 # to_remove.add(node)
        #                 # to_remove.add(other_node)
        #                 # to_add.add(new_node)
        #             if node.name.issubset(other_node.name):
        #                 # to_remove.add(node)
        #                 # to_remove.add(other_node)
        #                 old_nodes.remove(node)
        #                 old_nodes.remove(other_node)
        #                 new_node = Node(node.name & other_node.name)
        #                 new_node.documents = []
        #                 new_node.documents.extend(node.documents)
        #                 new_node.documents.extend([doc for doc in other_node.documents if doc not in new_node.documents])
        #                 to_add.add(new_node)
        #
        #     self.last_nodes = (self.last_nodes - to_remove) | to_add
        #     print(len(old_nodes))
        #
        # write_topics_to_xl("3.csv", self.last_nodes, with_children=True)

    def add_and_remove(self,principle):
        all_links = dict.fromkeys(list(self.last_nodes),{})
        to_remove = set()
        to_add = set()

        for node in self.last_nodes:
            countries = {d.country for d in node.documents}
            nodes_except_this = self.last_nodes - {node}
            news = dict.fromkeys(countries,set())
            for k in news.keys():
                for doc in node.documents:
                    if doc.country == k:
                        news[k].add(doc)

            for other_node in nodes_except_this:

                # if principle == "documents":
                #     common_documents = set(node.documents).intersection(set(other_node.documents))
                #     percent_1 = len(common_documents) / len(node.documents)
                #     percent_2 = len(common_documents) / len(other_node.documents)
                #     if percent_1 >= 0.5 and percent_2 >= 0.5:
                #         print(node.name, other_node.name)
                #         for cd in common_documents:
                #             print(translate(cd.title))
                #         print(percent_1, percent_2)
                #         all_links[node][other_node] = percent_1
                # elif principle == 'country':

                other_countries = {d.country for d in other_node.documents}

                common_documents = set(node.documents).intersection(set(other_node.documents))
                common_countries = {d.country for d in common_documents}
                percent_1 = len(common_countries) / len(countries)
                percent_2 = len(common_countries) / len(other_countries)
                # if common_countries:
                #     print(node.name, other_node.name)
                #     print(countries)
                #     print(other_countries)
                #     print(percent_1)
                #     print(percent_2)
                #     for cd in common_documents:
                #         print(cd.title)

                # other_news = dict.fromkeys(other_countries, set())
                # for k in other_news.keys():
                #         for doc in node.documents:
                #             if doc.country == k:
                #                 other_news[k].add(doc)
                #         if k in news.keys():
                #             print(node.name)
                #             print(other_node.name)
                #             l = [doc.title for doc in news[k] if doc in other_news[k]]
                #             print(l)
                #             if l:
                #
                #                 percent_1 += 1
                #                 percent_2 += 1
                #                 continue

                # percent_1 /= len(news.keys())
                # percent_2 /= len(other_news.keys())
                if percent_1 > 0.5 and percent_2 > 0.5:

                        all_links[node][other_node] = percent_1

        for node in self.last_nodes:
            try:
                print(node.name)
                for k,m in all_links[node].items():
                    print(k.name)
                    print(m)
                maximum_similarity_node = max(all_links[node].items(), key=operator.itemgetter(1))[0]

                del all_links[node][maximum_similarity_node]
                try:
                    del all_links[maximum_similarity_node]
                    new_node = Node(node.name | maximum_similarity_node.name)
                    new_node.children = [node, maximum_similarity_node]
                    new_node.subtopics = [node, maximum_similarity_node]
                    new_node.documents.extend(node.documents)
                    new_node.documents.extend([doc for doc in maximum_similarity_node.documents if doc not in new_node.documents])
                    to_remove.add(node)
                    to_remove.add(maximum_similarity_node)
                    to_add.add(new_node)
                except KeyError:
                    continue
            except KeyError:
                continue

        return to_remove, to_add


def check_free(nodes):
    for node in nodes:
        for ch in node.children:
            ch_percent = ch.percents[ch.parents.index(node)]
            for gch in ch.children:
                gchild_percent = gch.percents[gch.parents.index(ch)]
                if gchild_percent < ch_percent and gchild_percent < 0.5:
                    return ch
                elif gch.children:
                    return check_free(ch.children)
                else:
                    return gch


def write_topics_to_xl(fname, nodes, with_children=False):
    file = csv.writer(open(fname, "w"), delimiter=',')
    headers = ['Topic', 'News', 'Keywords']
    file.writerow(headers)
    for n in nodes:
        row = []
        if with_children:
            text = ''
            if n.subtopics:
                for c in n.subtopics:
                    text += ' '.join(c.name)
                    text += ' | '
            else:
                text = ' '.join(n.name)
        else:
            text = ' '.join(n.name)
        row.append(text)
        docs = n.documents
        for doc in docs:
            row.append(f"{doc.country} | {doc.title} | {doc.url} | {doc.translated}")
            row.append(' '.join(doc.named_entities))
        file.writerow(row)


def write_words_to_xl(fname, data):
    file = csv.writer(open(fname, "w"), delimiter=',')
    headers = ['Document', 'Deleted words']
    file.writerow(headers)

    for r in data:
        row = [r.translated, r.removed_words]
        file.writerow(row)


def write_start_words_to_xl(fname, data):
    file = csv.writer(open(fname, "w"))
    headers = ['Document', 'Deleted words']
    file.writerow(headers)

    for r in data:
        for key, ind in r.start_words.items():
            row = [key, ind]
            file.writerow(row)


if __name__ == '__main__':

    now = time.time()

    db = input("DB name: ")
    table = input("Table name: ")
    with_lead = input("With lead? ")
    types = tuple(input("What types? ").split())

    if not db:
        db = "day"
    if not table:
        table = "buffer"
    if with_lead == '':
        with_lead = False

    c = Corpus(db, table, with_lead=with_lead,analyze=types)
    c.find_topics()
    # write_words_to_xl("double_translation.csv", c.data)
    # write_start_words_to_xl("start_words.csv", c.data)

    t = Tree(c)
    t.find_last_topics()
    t.unite_similar_topics()
    write_topics_to_xl(f"{db}-topics.csv", t.last_nodes)
    f = open("time1.txt","w")
    f.write(str(time.time()-now))

