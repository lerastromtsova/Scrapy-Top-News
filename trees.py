import nltk
import sqlite3
import csv
import re
import time
import operator

from text_processing.preprocess import preprocess
from text_processing.translate import translate
# from text_processing.dates import process_dates


class Corpus:

    def __init__(self, db, table):

        self.table = table
        self.conn = sqlite3.connect(f"db/{db}.db")
        self.c = self.conn.cursor()
        self.c.execute("SELECT * FROM " + table)
        self.topics = []
        self.data = []

        raw_data = self.c.fetchall()

        for row in raw_data:
            self.data.append(Document(row,self.conn,table))

    def find_topics(self):

        for row1 in self.data:
            rows_except_this = [r for r in self.data if r.url != row1.url and r.country != row1.country]
            for row2 in rows_except_this:
                com_words = row1.named_entities.intersection(row2.named_entities)
                if len(com_words) and com_words not in self.topics:
                    self.topics.append(com_words)

        self.topics.sort(key=lambda s: -len(s))


class Document:

    def __init__(self,row,conn,table):

        self.country = row[0]
        self.title = row[1]
        # self.content = row[3]
        # self.url = row[4]
        # self.date = row[5]
        # self.translated = row[6]
        # self.double_translated = row[7]

        self.content = row[2]
        self.url = row[3]
        self.date = row[4]
        self.translated = row[5]
        self.double_translated = row[6]

        self.tokens = []

        self.conn = conn
        self.table = table

        if not self.translated or not self.double_translated:
            self.double_translate()

        for tr in preprocess(self.translated):
            if tr in preprocess(self.double_translated):
                self.tokens.append(tr)

        parse_tree = nltk.ne_chunk(nltk.tag.pos_tag(self.tokens), binary=True)  # POS tagging before chunking!
        self.named_entities = {k[0] for t in parse_tree.subtrees() for k in list(t) if t.label() == 'NE'}
        self.unite_countries()
        self.find_entities()
        self.unite_countries()
        # self.dates = process_dates(list(self.tokens)).append(self.date)

    def find_entities(self):

        text = re.findall(r"[\w]+|[^\s\w]",self.translated)
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

    def double_translate(self):

        n = 1500  # length limit
        if "Краткое описание: " in self.content:
            content = self.content.split("Краткое описание: ")[1]
        else:
            content = self.content

        # Split into parts of 1500 before translating
        content = [content[i:i + n] for i in range(0, len(content), n)]

        self.translated = ''
        self.double_translated = ''

        for c in content:

            eng_content = translate(c)
            orig_content = translate(eng_content, self.country)
            eng1_content = translate(orig_content)

            self.translated += ' '.join([self.translated,eng_content])
            self.double_translated += ' '.join([self.double_translated,eng1_content])

        c = self.conn.cursor()
        c.execute(f"UPDATE {self.table} SET translated=(?), translated1=(?) WHERE reference=(?)",
                  (self.translated,self.double_translated,self.url))
        self.conn.commit()


class Node:

    def __init__(self,item):

        self.name = item
        self.level = len(self.name)

        self.parents = []
        self.children = []
        self.documents = []
        self.percents = []

    def has_free_links(self,other_node):

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

    def unite_similar_topics(self):
        to_remove = set()
        to_add = set()
        all_links = {}
        for node in self.last_nodes:
            nodes_except_this = self.last_nodes - {node}
            for other_node in nodes_except_this:
                all_links[node] = {other_node: 0}
                common_documents = set(node.documents).intersection(set(other_node.documents))
                percent_of_common = 2*len(common_documents)/(len(node.documents)+len(other_node.documents))
                if percent_of_common >= 0.5:
                    all_links[node][other_node] = percent_of_common
                    # percent_of_potential = node.has_free_links(other_node)
                    # if percent_of_potential >= 0.5:

                if all_links[node][other_node] == 0:
                    del all_links[node][other_node]

        while all_links:

            for node in self.last_nodes:
                try:
                    print(node.name)
                    maximum_similarity_node = max(all_links[node].items(), key=operator.itemgetter(1))[0]
                    print("Max similarity: ", maximum_similarity_node.name)
                    del all_links[node][maximum_similarity_node]
                    new_node = Node(node.name|maximum_similarity_node.name)
                    new_node.documents = []
                    new_node.documents.extend(node.documents)
                    new_node.documents.extend([doc for doc in maximum_similarity_node.documents if doc not in new_node.documents])
                    to_remove.add(node)
                    to_remove.add(maximum_similarity_node)
                    to_add.add(new_node)
                except KeyError:
                    continue

        self.last_nodes = (self.last_nodes - to_remove) | to_add


def check_free(nodes):
    for node in nodes:
        for ch in node.children:
            ch_percent = ch.percents[ch.parents.index(node)]
            for gch in ch.children:
                gchild_percent = gch.percents[gch.parents.index(ch)]
                if gchild_percent < ch_percent and gchild_percent < 0.5:
                    return ch
                else:
                    return check_free(ch.children)


def write_topics_to_xl(fname, tree):
    file = csv.writer(open(fname, "w"))
    headers = ['Topic', 'News']
    file.writerow(headers)

    for node in tree.last_nodes:
                row = [' '.join(node.name)]
                for doc in node.documents:
                    row.append(f"{doc.url}: {doc.translated}")
                    row.append(' '.join(doc.named_entities))
                file.writerow(row)


if __name__ == '__main__':

    now = time.time()

    db = input("DB name: ")
    table = input("Table name: ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    c = Corpus(db,table)
    c.find_topics()

    t = Tree(c)
    t.find_last_topics()
    t.unite_similar_topics()
    write_topics_to_xl(f"{db}-topics.csv", t)

    print(time.time()-now)
