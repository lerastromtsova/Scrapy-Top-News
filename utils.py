import sqlite3
import re
import os


def create_file(filename):
    if not os.path.exists(filename):
        open(filename, 'w').close()


def create_dir(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


# COUNTRY functions

def iscountry(str):
    conn = sqlite3.connect("db/countries.db")
    c = conn.cursor()

    """ Turn on for city checking """
    # c.execute("SELECT name, name_ascii FROM cities")
    # res = c.fetchone()
    # while res:
    #     if str in res:
    #         return True
    #     res = c.fetchone()

    c.execute("SELECT name FROM state")
    res = c.fetchone()
    while res:
        if str in res:
            return True
        res = c.fetchone()

    c.execute("SELECT country FROM countries")
    res = c.fetchone()
    while res:
        if str in res or str.upper() in res:
            return True
        res = c.fetchone()

    return False


def is_any_in_countries(str):
    conn = sqlite3.connect("db/countries.db")
    c = conn.cursor()
    c.execute("SELECT * FROM cities")
    res = c.fetchone()
    while res:
        low = [w.value.lower() for w in res if w is not None]
        if str.lower() in low:
            return True
        res = c.fetchone()
    return False

def count_countries(name):
    countries = {w for w in name if iscountry(w.upper()) or iscountry(w)}
    return len(countries)


def count_not_countries(name):
    countries = {w for w in name if iscountry(w.upper()) or iscountry(w)}
    not_countries = name - countries
    return len(not_countries)


# FIO functions

def isfio(strr):
    if strr[0].isupper() and ' ' in strr and not iscountry(strr):
        return True
    conn = sqlite3.connect("db/fio.db")
    c = conn.cursor()
    c.execute("SELECT * FROM fio")
    res = c.fetchone()
    while res:
        name = res[0]
        surname = res[1]
        middle_name = res[2]
        country = res[3]
        if strr == surname:
            return True
        if name and surname:
            if strr == name + " " + surname:
                return True
        res = c.fetchone()
    return False


def replace_presidents(text, mode="add"):

    conn = sqlite3.connect("db/fio.db")
    c = conn.cursor()
    c.execute("SELECT * FROM fio")
    res = c.fetchone()

    to_add = set()
    to_remove = set()

    while res:

            name = res[0]
            surname = res[1]
            middle_name = res[2]
            country = res[3]
            for word in text:
                if word == surname:
                    if mode == "add":
                        to_add.add(country)
                    if mode == "remove":
                        to_remove.add(word)
                if name and surname:
                    if word == name + " " + surname or name + " " + surname in word:
                        if mode == "add":
                            to_add.add(country)
                        if mode == "remove":
                            to_remove.add(word)
            res = c.fetchone()

    text |= to_add
    text -= to_remove

    return text


# INTERSECTION functions

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
                                try:
                                    new1.remove(s1)
                                    new1.add(s2)
                                except KeyError:
                                    pass
                        else:
                            if s2 in new2:
                                try:
                                    new2.remove(s2)
                                    new2.add(s1)
                                except KeyError:
                                    pass
                if len(words_2) == 1:
                    cw = words_1.intersection(words_2)
                    if cw:
                        try:
                            new1.remove(s1)
                            new1.add(s2)
                        except KeyError:
                            pass
            if len(words_1) == 1:
                if len(words_2) >= 2:
                    cw = words_1.intersection(words_2)
                    if cw:
                        try:
                            new2.remove(s2)
                            new2.add(s1)
                        except KeyError:
                            pass
    return new1.intersection(new2)


def intersect(set1, set2):
    new1 = set1.copy()
    new2 = set2.copy()
    for s1 in set1:
        for s2 in set2:
            if s2.lower() == s1.lower()+'s' or s2.lower() == s1.lower()+'es' or s2.lower() == s1.lower()+'ies' or s2.lower() == s1.lower()+'er':
                if s2 in new2:
                    new2.remove(s2)
                new2.add(s1)
            elif s1.lower() == s2.lower()+'s' or s1.lower() == s2.lower()+'es' or s1.lower() == s2.lower()+'ies' or s1.lower() == s2.lower()+'er':
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


def intersection_with_substrings(set1, set2):
    result_set = set()
    for item1 in set1:
        for item2 in set2:
            if item1 == item2:
                result_set.add(item1)
            elif item1 in item2.split():
                result_set.add(item2)
            elif item2 in item1.split():
                result_set.add(item1)
    return result_set


def sublist(l1, l2):
    s1 = ''.join(map(str, l1))
    s2 = ''.join(map(str, l2))
    return re.search(s1, s2)


def unite_news_text_and_topic_name(news_text, topic_name):
    inters = set()
    for word in topic_name:
        for word2 in news_text:
            if word == word2:
                inters.add(word)
            elif word2 in word.split():
                if len(word.split()) >= 2:
                    idx = word.split().index(word2)
                    if idx != 0:
                        inters.add(word)

    return inters


# COMMON utils
class ContinueI(Exception):
    pass


def get_other(number):
    if number == 1:
        return 0
    return 1


def exists(object):
    if object:
        return 1
    return 0


def more_than_one(object):
    if len(object) > 1:
        return 1
    return 0


# DB utils
def add_column(table, column_name, length, cursor):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} TEXT({length})")
    except sqlite3.OperationalError:
        pass


# Working with topic name
def delete_redundant(name):
    name = {w for w in name if not any(word for word in name-{w} if set(w.lower().split()).issubset(set(word.lower().split())))}
    return name


# Plotting utils
def get_topic_news_nodes(topics):
    nodes = list()
    edges = list()
    number = 0

    for t in topics:
        node_object = {"name": t.name}
        nodes.append(node_object)
        topic_number = number
        number += 1
        for n in t.news:
            node_object = {"title": n.translated['title'],
                           "url": n.url,
                           "country": n.country}
            nodes.append(node_object)
            edges.append((topic_number, number))
            number += 1
    return nodes, edges


def get_topic_subtopic_nodes(topics):
    nodes = list()
    edges = list()
    number = 0
    for t in topics:
        node_object = {"name": t.name}
        nodes.append(node_object)
        topic_number = number
        number += 1
        for s in t.subtopics:
            node_object = {"name": s.name}
            nodes.append(node_object)
            subtopic_number = number
            edges.append((topic_number, subtopic_number))
            number += 1
            for n in s.news:
                node_object = {"title": n.translated['title'],
                               "url": n.url,
                               "country": n.country}
                nodes.append(node_object)
                edges.append((subtopic_number, number))
                number += 1
        if not t.subtopics:
            for n in t.news:
                node_object = {"title": n.translated['title'],
                               "url": n.url,
                               "country": n.country}
                nodes.append(node_object)
                edges.append((topic_number, number))
                number += 1
    return nodes, edges