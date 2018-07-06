import time

import nltk

from data_classes import Corpus, Document
from xl_stats import write_tz, write_topics_with_freq, write_topics_to_xl


class Node:

    def __init__(self, item):

        self.name = item
        self.level = len(self.name)

        self.parents = []
        self.children = []
        self.documents = []
        self.percents = []
        self.subtopics = []

        self.main_documents = {}
        self.main_words = set()

    def replace_similar(self):

        replace_dict = set()


        for doc in self.documents:

            for word in doc.description:
                if len(word.split()) > 1:
                    replace_dict.add(word)
        for doc in self.documents:
            to_remove = set()
            to_add = set()
            for word in doc.description:
                for key in replace_dict:
                    if word in key:
                        to_remove.add(word)
                        to_add.add(key)
            doc.description -= to_remove
            doc.description |= to_add


    def has_free_links(self, other_node):

        topic = self.name
        my_free_words = [d.named_entities['content'] - topic for d in self.documents]
        suit_documents = [sd for sd in self.documents if sd not in other_node.documents]
        par_free_words = [pd.named_entities['content'] - topic for pd in suit_documents]
        connection = 0

        for doc in my_free_words:
            for d in par_free_words:
                if doc.intersection(d):
                    connection += 1

        if my_free_words and par_free_words:
            percent_of_connected = connection/(len(my_free_words)*len(par_free_words))
            return percent_of_connected
        return 0

    def find_most_frequent(self, type):
        freq_words = {}
        for document in self.documents:
            descr = document.description

            if type == 'lowercase':
                parse_tree = nltk.ne_chunk(nltk.tag.pos_tag(descr),
                                           binary=True)  # POS tagging before chunking!

                nes = {k[0] for branch in parse_tree.subtrees() for k in list(branch) if
                                            branch.label() == 'NE'}
                descr = [d for d in descr if d not in nes]

            for word in descr:

                countries = {d.country for d in self.documents if word in d.tokens['lead'] or word in d.tokens['title']}
                if len(countries) >= 2:

                    if word in freq_words.keys():
                        freq_words[word] += 1
                    else:
                        freq_words[word] = 1

        if freq_words:
            maxval = max(freq_words.values())
            result = {key: value for key, value in freq_words.items() if value == maxval}
            return result
        else:
            return freq_words

    def add_document(self, doc):
        self.documents.append(doc)

    def assign_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)
            self.percents.append(self.has_free_links(parent))

    def assign_child(self, child):
        if child not in self.children:
            self.children.append(child)
            self.subtopics.extend(child.subtopics)


    def isparent(self, other_node):
        if other_node in self.parents:
            return True
        return False

    def ischild(self, other_node):
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

    def __init__(self, corpus):

        self.nodes = [Node(item) for item in corpus.topics]
        self.assign_documents(corpus)
        self.db = corpus.db

        for node in self.nodes:

            for other_node in [n for n in self.nodes if n != node]:

                if node.name.issubset(other_node.name) and node not in other_node.children and not node.contains(other_node.children):
                    node.assign_parent(other_node)
                    other_node.assign_child(node)

                if other_node.name.issubset(node.name) and node not in other_node.parents and not other_node.contains(node.children):
                    other_node.assign_parent(node)
                    node.assign_child(other_node)

        self.roots = [n for n in self.nodes if n.isroot()]
        self.leaves = [n for n in self.nodes if n.isleaf()]
        write_topics_to_xl("0.xlsx", self.roots)
        self.last_nodes = set(self.roots)
        for node in self.last_nodes:
            node.replace_similar()

    def assign_documents(self, corpus):

        for node in self.nodes:
            for doc in corpus.data:
                if node.name.issubset(doc.named_entities['content']):
                    node.add_document(doc)

    def find_last_topics(self):
        for root in self.roots:
            x = check_free([root])
            if x:
                self.last_nodes.add(x)
        write_topics_to_xl("2-3.xlsx", self.last_nodes)
        write_tz(self)


    def unite_similar_topics(self):

        """ 1) «Хотя бы для одной новости эта тема важна? (ведь международные новости это громкие события)»"""

        to_remove = set()
        for node in self.last_nodes:
            at_least_one = False
            for doc in node.documents:
                if doc.description.intersection(node.name):
                    at_least_one = True
            if not at_least_one:
                to_remove.add(node)
        self.last_nodes -= to_remove

        write_topics_to_xl("1-1.xlsx", self.last_nodes)

        """ 2) «Для какой новости эта общая тема ближе всего?» """

        for node in self.last_nodes:
            similarity_dict = {}
            for doc in node.documents:
                sim = len(doc.description.intersection(node.name))
                similarity_dict[doc] = sim
            node.main_documents = {d for d in node.documents if similarity_dict[d] == max(similarity_dict.values())}
            print(node.name, len(node.main_documents))



        """ 3) «Какие новости останутся в теме?» 
        Если выполняется хотя бы один из трех признаков - проверяемая новость остается: 
         а) Если между кратким описанием главной новости и кратким описанием проверяемой новости – есть общие слова (общие слова записываются к данной теме)  """
        """
               б) Если между кратким описанием главной новости и текстом статьи проверяемой новости - есть общие слова (общие слова записываются к данной теме)  
               в) Если между текстом статьи главной новости и кратким описанием проверяемой новости - есть общие слова (общие слова записываются к данной теме)  
               -) Если новость остается одна в теме - то тема удаляется.  
               -) Если новости одной страны остаются в теме – то тема удаляется 
               """

        to_remove = set()

        for node in self.last_nodes:
            docs_to_remove = set()
            for doc in node.documents:
                common_words_in_descr = set()
                common_words_in_d1_c2 = set()
                common_words_in_c1_d2 = set()
                for main_doc in node.main_documents:
                    common_words_in_descr.update(doc.description.intersection(main_doc.description))
                    node.main_words.update(common_words_in_descr)
                    common_words_in_d1_c2.update(doc.tokens['content'].intersection(main_doc.description))
                    node.main_words.update(common_words_in_d1_c2)
                    common_words_in_c1_d2.update(doc.description.intersection(main_doc.tokens['content']))
                    node.main_words.update(common_words_in_c1_d2)
                if not common_words_in_descr and not common_words_in_c1_d2 and not common_words_in_d1_c2:
                    docs_to_remove.add(doc)
            node.documents = [d for d in node.documents if d not in docs_to_remove]

        write_topics_to_xl("1-3-1.xlsx", self.last_nodes)

        for node in self.last_nodes:
            countries = {d.country for d in node.documents}
            if len(countries) < 2:
                to_remove.add(node)

        self.last_nodes -= to_remove

        write_topics_to_xl("1-3-2.xlsx", self.last_nodes)

    def final_unite(self):
        """4) «Какие темы объединяются?»  
        Объединяются те темы, что имеют общие новости между друг другом и при этом выполняют два условия:  
        а) их общие слова тем (от а,б,в пунктов №1) хотя бы один раз совпадают (одним словом). 
        Итерации происходят до тех пор, пока не останется новостей, способных объединиться 
         б) есть хотя бы одно общее слово между двумя комбинациями слов общих тем  """

        most_similar = []

        while self.last_nodes:
            node = self.last_nodes.pop()
            others = self.last_nodes - {node}
            similar = [node]
            while others:
                other = others.pop()

                common_words = node.main_words.intersection(other.main_words)

                if len(common_words) >= 1:
                    if node.name.intersection(other.name):
                            self.last_nodes.remove(other)
                            similar.append(other)

            most_similar.append(similar)

        for ms in most_similar:
            name = set()
            docs = set()
            subtopics = []
            for s in ms:
                name |= s.name
                docs |= set(s.documents)
                subtopics.append(s)

            node = Node(name)
            node.documents = docs
            node.subtopics = subtopics
            self.last_nodes.add(node)


    def unite_until_done(self):
        prev = set()
        iter = 0
        while len(self.last_nodes) != len(prev):
            iter += 1
            # print(iter)
            # print(len(prev))
            # print(len(self.last_nodes))
            prev = self.last_nodes.copy()
            self.final_unite()
            write_topics_to_xl(f"1-4-{iter}.xlsx", self.last_nodes, with_children=True)

    def delete_subsets(self):
        to_remove = set()

        for n in self.last_nodes:
            other_nodes = self.last_nodes - {n}
            for on in other_nodes:
                if n.name.issubset(on.name) and on not in to_remove:
                    to_remove.add(n)

        return to_remove

def have_common_words(set1,set2):
    if set1.intersection(set2):
        return True
    return False


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


if __name__ == '__main__':

    now = time.time()

    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    c = Corpus(db, table)
    c.delete_news()
    c.find_topics()

    t = Tree(c)
    t.unite_similar_topics()
    t.unite_until_done()

    f = open("time1.txt", "w")
    f.write(str(time.time()-now))