import time

import nltk
import sqlite3

from dclasses_deutsch import Corpus, Document
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

    def find_main_documents(self):
        similarity_dict = {}
        for doc in self.documents:
            sim = len(doc.description.intersection(self.name))
            similarity_dict[doc] = sim
        self.main_documents = {d for d in self.documents if similarity_dict[d] == max(similarity_dict.values())}

    def find_main_words(self):
        for doc in self.documents:
            others = [d for d in self.documents if d.country != doc.country]
            for other in others:
                com_words = doc.descr_without_countries.intersection(other.descr_without_countries)
                if com_words:
                    self.main_words.update(com_words)


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
        write_topics_to_xl("0.xls", self.roots)
        write_topics_to_xl("0.xlsx", self.roots)
        self.last_nodes = set(self.roots)
        for node in self.last_nodes:
            node.replace_similar()
            node.find_main_documents()
            # node.find_main_words()

    def assign_documents(self, corpus):

        for node in self.nodes:
            for doc in corpus.data:
                if node.name.issubset(doc.description):
                    node.add_document(doc)


    def unite_similar_topics(self):

        """2) Проверяем темы. Темы остаются если одно из правил выполняется:
         а) есть общее слово в кратких описаниях хотя бы между двумя разными странами (общие слова записываются)  КРОМЕ СТРАН 
        б) Для каждой темы выбирается главная новость, краткое описание которой больше всего связано с общей темой. 
        Тема сохраняется: 
        - Если между кратким описанием главной новости и текстом статьи (другой страны) проверяемой новости -
         есть общие слова (общие слова не должны совпадать со словами из библиотеки стран (кроме городов))  
         - Если между текстом статьи главной новости и кратким описанием проверяемой новости (другой страны) -
          есть общие слова (общие слова не должны совпадать со словами из библиотеки стран (кроме городов))  
          -) Если новость остается одна в теме - то тема удаляется.
           -) Если новости одной страны остаются в теме – то тема удаляется  """

        to_remove = set()

        for node in self.last_nodes:

                for doc in node.documents:
                    common_words_in_descr = set()
                    common_words_in_d1_c2 = set()
                    common_words_in_c1_d2 = set()
                    for main_doc in node.main_documents:
                        if doc.country != main_doc.country:
                            common_words_in_descr.update(doc.descr_without_countries.intersection(main_doc.descr_without_countries))
                            node.main_words.update(common_words_in_descr)
                            common_words_in_d1_c2.update(doc.tokens['content'].intersection(main_doc.descr_without_countries))
                            node.main_words.update(common_words_in_d1_c2)
                            common_words_in_c1_d2.update(doc.descr_without_countries.intersection(main_doc.tokens['content']))
                            node.main_words.update(common_words_in_c1_d2)
                    if not common_words_in_descr and not common_words_in_c1_d2 and not common_words_in_d1_c2:
                        to_remove.add(node)
        self.last_nodes -= to_remove
        write_topics_to_xl("2.xlsx", self.last_nodes, with_children=False)
        write_topics_to_xl("2.xls", self.last_nodes, with_children=False)

        """
          4) Далее проверяем, есть ли у более чем 50% всех новостей найденные ранее общие слова темы КРАТКОЕ ОПИСАНИЕ (общие слова пункта 2а и 2б). 
        Если хотя бы какие-то общие слова есть у более чем 50% новостей темы, то тема остается, если меньше - то удаляется. 
        Все новости, что не имеют общих слов с общей темой проверяются на наличие общих слов с кратким описанием главной новости 
        (если у проверяемой новости в кратком описании есть общее слово с главной новостью, то проверяемая новость остается)."""
        to_remove = set()

        for node in self.last_nodes:
            perc = 0
            has_these_words = set()
            for doc in node.documents:
                cw = doc.descr_without_countries.intersection(node.main_words)
                if len(cw) >= 1:
                    perc += 1
                    has_these_words.add(doc)
            perc /= len(node.documents)
            if perc < 0.5:
                to_remove.add(node)
            else:
                rest = {d for d in node.documents if d not in has_these_words}
                for doc in rest:
                    if not any([doc.descr_without_countries.intersection(md.descr_without_countries) for md in node.main_documents]):
                        node.documents.remove(doc)

        self.last_nodes -= to_remove
        write_topics_to_xl("4.xlsx", self.last_nodes, with_children=False)
        write_topics_to_xl("4.xls", self.last_nodes, with_children=False)




    def final_unite(self):
        """
                  5) Далее объединяем темы только в том случае,
                 а) если хотя бы две новости из разных стран совпадают.  
                б) или если есть одна общая новость между темами, то проверяем на взаимное наличие общих слов (найденных во 2 пункте).
                Если у более чем 50 % новостей одной темы есть хотя-бы одно общее слово (из пункта 2 другой темы), то проверяется обратная связь.
                Если взаимная связь общих слов подтверждается у той и другой новости в больше чем 50 % новостей - значит темы объединяются. """

        most_similar = []

        while self.last_nodes:
            node = self.last_nodes.pop()
            others = self.last_nodes - {node}
            similar = [node]
            while others:
                other = others.pop()

                common_documents = [doc for doc in node.documents if doc in other.documents]
                common_countries = {d.country for d in common_documents}

                if len(common_countries) >= 2:

                    self.last_nodes.remove(other)
                    similar.append(other)

                elif len(common_countries) == 1:
                    percent1 = 0
                    percent2 = 0

                    for doc in node.documents:
                        if doc.descr_without_countries.intersection(other.main_words):
                            percent1 += 1
                    percent1 /= len(node.documents)

                    for doc in other.documents:
                        if doc.descr_without_countries.intersection(node.main_words):
                            percent2 += 1
                    percent2 /= len(node.documents)

                    if percent1>=0.5 and percent2>=0.5:
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
            write_topics_to_xl(f"5-{iter}.xlsx", self.last_nodes, with_children=True)
            write_topics_to_xl(f"5-{iter}.xls", self.last_nodes, with_children=True)

    def delete_subsets(self):
        to_remove = set()

        for n in self.last_nodes:
            other_nodes = self.last_nodes - {n}
            for on in other_nodes:
                if n.name.issubset(on.name) and on not in to_remove:
                    to_remove.add(n)

        return to_remove



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

    c.find_topics()

    t = Tree(c)
    t.unite_similar_topics()
    t.unite_until_done()

    f = open("time1.txt", "w")
    f.write(str(time.time()-now))