from descr import count_countries, count_not_countries
from corpus import Corpus, Topic
from xl_stats import write_topics
from datetime import datetime
from descr import intersect, iscountry
from math import ceil
from text_processing.preprocess import PUNKTS
from string import punctuation
import sqlite3
import re
from document import COUNTRIES
import itertools
from text_processing.preprocess import STOP_WORDS, check_first_entities

with open("text_processing/between-words.txt", "r") as f:
    BETWEEN_WORDS = f.read().split('\n')


def similar(topics):
    new_topics = list()

    for t in topics:
        if t is not None:
            others = []
            for to in topics:
                if to and set(to.news) != set(t.news):
                    others.append(to)

            similar = {t}
            freq_words = t.most_frequent()
            freq_words = freq_words[:ceil(len(freq_words) / 2)]

            for o in others:
                if o is not None:
                    try:

                        common_words = t.name.intersection(o.name)
                        common_news = set(t.news).intersection(set(o.news))
                        news_countries = {n.country for n in common_news}
                        where = {w for w in common_words if iscountry(w)}
                        who = {w for w in common_words if w[0].isupper() and not iscountry(w)}
                        what = {w for w in common_words if w[0].islower()}
                        cw_in_unique = t.new_name.intersection(o.new_name)
                        freq_words1 = o.most_frequent()
                        freq_words1 = freq_words1[:ceil(len(freq_words1) / 2)]
                        common_freq = intersection_with_substrings(freq_words1, freq_words)

                        # a
                        if len(where) >= 1 and len(who) >= 1 and len(what) >= 2:
                            print("A", o.name, t.name)
                            similar.add(o)
                            continue

                        # b
                        if len(where) >= 1 and len(who) >= 1 and len(what) >= 1 and len(common_news) >= 1:
                            print("B", o.name, t.name)
                            similar.add(o)
                            continue

                        # c
                        if len(news_countries) >= 2:
                            print("C", o.name, t.name)
                            similar.add(o)
                            continue

                        # d
                        if len(where) >= 1 and not who and len(what) >= 3:
                            print("D", o.name, t.name)
                            similar.add(o)
                            continue

                        # e
                        if len(where) >= 1 and not who and len(what) >= 2 and len(common_news) >= 1:
                            print("E", o.name, t.name)
                            similar.add(o)
                            continue

                        # f
                        if len(cw_in_unique) / len(t.new_name) > 0.5 and len(cw_in_unique) / len(o.new_name) > 0.5:
                            print("F", o.name, t.name)
                            similar.add(o)
                            continue

                        # g
                        if (len(common_freq) / len(freq_words) > 0.5 and len(common_freq) / len(
                                freq_words1) > 0.5) and len(cw_in_unique) >= 1:
                            print("G", o.name, t.name)
                            similar.add(o)

                    except ZeroDivisionError:
                        continue

            new_topic = Topic(t.name, init_news=t.news)
            for s in similar:
                new_topic.name.update(s.name)
                new_topic.main_words.update(t.main_words.intersection(s.main_words))
                new_topic.new_name.update(t.new_name.intersection(s.new_name))
                for n in s.news:
                    if n not in new_topic.news:
                        new_topic.news.extend(s.news)
                new_topic.subtopics.add(s)
                new_topic.most_frequent()
                topics[topics.index(s)] = None

            new_topic.news = list(set(new_topic.news))
            new_topics.append(new_topic)

    return new_topics


# def give_news(topics, rows):
#     for row in rows:
#
#         for topic in topics:
#
#             a = b = c = False
#
#
#             for new in topic.news:
#                 cw_all = set(row.all_text).intersection(set(new.all_text))
#                 cw_unique = {w for w in cw_all if w in topic.new_name}
#
#                 if count_countries(cw_all) >= 1 and count_not_countries(cw_all-cw_unique) >= 2:
#
#                     if len(cw_unique) >= 2:
#
#                         if row not in topic.news:
#
#                             a = True
#
#             freq_words_50 = topic.most_frequent()[:ceil(len(topic.frequent) / 2)]
#
#             cw_freq_50 = set(row.all_text).intersection(set(freq_words_50))
#             if len(cw_freq_50)/len(freq_words_50) > 0.5:
#                 if row not in topic.news:
#                     b = True
#
#             cw_unique = set(row.all_text).intersection(set(topic.unique_words))
#             if len(cw_unique) >= 1:
#                 c = True
#
#             if a & b | c:
#                 if row not in topic.news:
#                     topic.news.append(row)
#
#             # keywords = {w for w in topic.unique_words if w in row.description}
#             # if (percent1 > 0.5 and percent3 > 0.5 or percent2 > 0.5 and percent4 > 0.5) and len(keywords) >= 1:
#             #     if row not in topic.news:
#             #         topic.news.append(row)
#     for topic in topics:
#         topic.news = delete_dupl_from_news(topic.news)
#
#     topics = delete_duplicates(topics)
#
#     return topics


def assign_news(topics, rows):
    for row in rows:

        for topic in topics:

            cw_unique = {w for w in row.all_text if w in topic.new_name}

            if cw_unique:
                common_words = topic.name.intersection(row.all_text)
                where = {w for w in common_words if iscountry(w)}
                who = {w for w in common_words if w[0].isupper() and not iscountry(w)}
                what = {w for w in common_words if w[0].islower()}
                if len(where) >= 1 and (len(who) >= 1 and len(what) >= 2 or len(what) >= 3):
                    print("a")
                    print(topic.name)
                    print(row.id)
                    print(where, who, what)

                    topic.news.append(row)

                freq_words_50 = topic.most_frequent()[:ceil(len(topic.frequent) / 2)]
                cw_freq_50 = set(row.all_text).intersection(set(freq_words_50))

                try:

                    if len(cw_freq_50) / len(freq_words_50) > 0.5:
                        if len(where) >= 1 and len(who) >= 1 and len(what) >= 1:
                            if row not in topic.news:
                                print("b")
                                print(topic.name)
                                print(row.id)
                                print(where, who, what)
                                print(cw_freq_50)
                                topic.news.append(row)

                except ZeroDivisionError:
                    continue

    for topic in topics:
        topic.news = delete_dupl_from_news(topic.news)

    topics = delete_duplicates(topics)

    return topics


def delete_duplicates(topics):
    for i, t in enumerate(topics):
        if t:
            others = [to for to in topics if to is not None]
            others = [to for to in others if t != to]
            ids = {new.id for new in t.news}
            for o in others:
                if o:
                    other_ids = {n.id for n in o.news}
                    if ids == other_ids:
                        topics[i] = None
    topics = [t for t in topics if t is not None]
    return topics


def redefine_unique(topics):
    for topic in topics:
        other_topics = [t for t in topics if t != topic]
        for ot in other_topics:
            cw = intersection_with_substrings(topic.name, ot.name)
            percent1 = len(cw) / len(topic.name)
            percent2 = len(cw) / len(ot.name)
            cw2 = intersection_with_substrings(topic.main_words, ot.main_words)
            percent3 = len(cw2) / len(topic.main_words)
            percent4 = len(cw2) / len(ot.main_words)

            if count_countries(cw) >= 1 and percent1 > 0.5 and percent2 > 0.5 and percent3 > 0.5 and percent4 > 0.5:

                print("Similar", topic.name, ot.name)
                continue
            else:
                topic.new_name -= cw
                if "Crimea" in topic.name:
                    print("Not Similar")
                    print(topic.name)
                    print(ot.name)
                    print(cw)
                    print("Unique words", topic.new_name)

        # topic.new_name = split_into_single(topic.new_name)
        print("Unique words", topic.new_name)

    to_remove = set()

    for topic in topics:
        if len(topic.new_name) < 1 or count_not_countries(topic.new_name) == 0:
            print("Deleting:")
            print(topic.name)
            print(topic.new_name)
            to_remove.add(topic)

    topics = [t for t in topics if t not in to_remove]
    return topics


def delete_dupl_from_news(news_list):
    new = list()
    for n in news_list:
        ids = {i.id for i in new}
        if n.id not in ids:
            new.append(n)
    return new


def find_objects(topics):
    new_topics = set()

    for topic in topics:

        for new in topic.news:

            objects = new.description.intersection(topic.new_name)

            if len(objects) >= 1:
                topic.objects.update(objects)
                new_topics.add(topic)

            for new1 in topic.news:

                if new != new1:

                    for i in range(len(new.sentences)):
                        for j in range(len(new1.sentences)):

                            unique_cw = {w for w in topic.new_name if w in new.sentences[i] and w in new1.sentences[j]}

                            if unique_cw:

                                # par = new.sentences[i]
                                # try:
                                #     par += " "
                                #     par += new.sentences[i-1]
                                # except IndexError:
                                #     pass
                                # try:
                                #     par += " "
                                #     par += new.sentences[i+1]
                                # except IndexError:
                                #     pass
                                #
                                # par1 = new1.sentences[j]
                                # try:
                                #     par1 += " "
                                #     par1 += new1.sentences[j - 1]
                                # except IndexError:
                                #     pass
                                # try:
                                #     par1 += " "
                                #     par1 += new1.sentences[j + 1]
                                # except IndexError:
                                #     pass
                                #
                                # cw = intersect(set(par.split()), set(par1.split()))

                                cw = intersect(set(new.sentences[i].split()), set(new1.sentences[j].split()))

                                not_unique_cw = {word for word in cw - unique_cw if word[0].islower()}

                                if unique_cw and not_unique_cw:
                                    topic.obj.update(cw)
                                    new_topics.add(topic)

        cw_in_descr = topic.news[0].description.intersection(topic.news[1].description)

        topic.objects = {o for o in topic.objects if len(o) > 2}
        topic.obj = {o for o in topic.obj if len(o) > 2}

        if all(True if w[0].isupper() else False for w in topic.name):
            topic.name.update(topic.obj)

        if count_countries(cw_in_descr) >= 1 and count_not_countries(cw_in_descr) >= 2:
            new_topics.add(topic)

    return list(new_topics)


def extend_topic_names(topics):
    for topic in topics:
        if all(True if w[0].isupper() else False for w in topic.name):
            topic.name.update(topic.news[0].description.intersection(topic.news[1].description))

        if len([w for w in topic.name if w[0].islower()]) >= 1:
            topic.name.update(
                topic.news[0].named_entities['content'].intersection(topic.news[1].named_entities['content']))

    return topics


def unite_countries_in(data):
    conn = sqlite3.connect("db/countries.db")
    c = conn.cursor()
    c.execute("SELECT * FROM countries")
    all_rows = c.fetchall()
    to_remove = set()
    to_add = set()

    for ent in data:
        for row in all_rows:
            low = [w.lower() for w in row if w is not None]

            if ent:
                if ent.lower() in low and ent != row[0]:

                    to_remove.add(ent)
                    to_add.add(row[0])
                if len(ent) <= 1:
                    to_remove.add(ent)

            if len(ent.lower().split()) > 1 and ent != row[0]:
                for e in ent.lower().split():
                    if e in low:
                        to_remove.add(ent)
                        to_add.add(row[0])

    data = (data - to_remove) | to_add

    # data -= to_remove
    # data.update(to_add)

    return data


TITLES = {"President", "Chancellor", "Democrat", "Governor", "King", "Queen", "Ministry", "Minister"}


def find_all_uppercase_sequences(words_list):
    seq = {' '.join(b) for a, b in itertools.groupby(words_list, key=lambda x: x[0].isupper() and x.lower() not in STOP_WORDS) if a}
    return seq


def add_words_to_topics(topics):

    for topic in topics:
        sent_dict = dict.fromkeys(list(range(len(topic.news))))

        for word in topic.new_name:

            common_words = set()

            for i, new in enumerate(topic.news):
                sent_dict[i] = {word: [w for w in sent.split() for sent in new.sentences if word in sent]}

            for i, new in enumerate(topic.news):
                common_words &= sent_dict[i][word]

            topic.name.add(common_words)

    return topics


def unite_fio(topics):
    for topic in topics:

        fios = set()

        text1 = topic.news[0].all_text_splitted.copy()
        strings_to_check1 = find_all_uppercase_sequences(text1)

        text2 = topic.news[1].all_text_splitted.copy()
        strings_to_check2 = find_all_uppercase_sequences(text2)

        common_strings = strings_to_check1.intersection(strings_to_check2)

        fios.update(common_strings)

        short_strings1 = {w for w in strings_to_check1 if len(w.split()) <= 2}

        short_strings2 = {w for w in strings_to_check2 if len(w.split()) <= 2}

        for word1 in short_strings1:
            for word2 in short_strings2:
                if word1 in word2:
                    if any(w for w in strings_to_check1 if word1 in w):
                        pass
                    else:
                        fios.add(word2)
                elif word2 in word1:
                    if any(w for w in strings_to_check2 if word2 in w):
                        pass
                    else:
                        fios.add(word1)

        topic.news[0].all_text.update(set(fios))
        topic.news[1].all_text.update(set(fios))

        topic.name = intersection_with_substrings(topic.news[0].all_text, topic.news[1].all_text)
        name = topic.name.copy()

        name = unite_countries_in(name)

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        ids, _ = topic.ids(topic.name)

        short_to_check = {w for w in name if len(w.split()) == 1 and w not in COUNTRIES and w[0].isupper()}

        long = name - short_to_check

        checked_entities = check_first_entities(short_to_check)
        checked_lower = {w for w in checked_entities.keys() if not checked_entities[w]}
        checked_upper = {w for w in checked_entities.keys() if checked_entities[w]}

        name = long | checked_upper
        name = name | checked_lower

        topic.name = name
        # print(topic.name)
        topic.new_name = topic.name.copy()
        # print(topic.name)

    return topics


def filter_topics(topics):

    positive = set()
    negative = set()
    neutral = set()

    for topic in topics:
        # All words
        all_words, num_all_words = topic.all_words(topic.name)
        if num_all_words >= 9:
            positive.add(topic)
            topic.method.add('9 "ВСЕ СЛОВА" - проходит ')
            continue
        elif num_all_words <= 1:
            negative.add(topic)
            continue

        # All w/o countries
        all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        if num_all_wo_countries >= 5:
            positive.add(topic)
            topic.method.add('5 "ВСЕ СЛОВА – Страны" - проходит')
            continue
        elif num_all_wo_countries <= 1:
            negative.add(topic)
            continue

        # All w/o small & countries
        all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_countries_and_small(all_words)
        if num_all_wo_small_and_countries >= 5:
            positive.add(topic)
            topic.method.add('5 "ВСЕ СЛОВА - Прописные и Страны" - проходит ')
            continue

        # FIO
        fio, num_fio = topic.fio(all_words)
        if num_fio >= 3:
            positive.add(topic)
            topic.method.add('3 "ФИО" - проходит ')
            continue

        # Big letter
        big, num_big = topic.big(all_words)
        if num_big >= 4:
            positive.add(topic)
            topic.method.add('4 "ЗАГЛАВНЫЕ" - проходит ')
            continue

        # Small - already count
        small, num_small = topic.small(all_words)
        if num_small >= 5:
            positive.add(topic)
            topic.method.add('5 "ПРОПИСНЫЕ" - проходит ')
            continue

        # Countries - already count
        countries, num_countries = topic.countries(all_words)
        if num_countries >= 5:
            positive.add(topic)
            topic.method.add('5 "СТРАНЫ" - проходит ')
            continue

        # All unique
        unique_words, num_unique_words = topic.all_words(topic.new_name)
        if num_unique_words >= 5:
            positive.add(topic)
            topic.method.add('5 "ВСЕ УНИКАЛЬНЫЕ" - проходит ')
            continue
        elif num_unique_words == 0:
            negative.add(topic)
            continue

        # Unique w/o countries
        unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        if num_unique_wo_countries >= 5:
            positive.add(topic)
            topic.method.add('5 "ВСЕ УНИКАЛЬНЫЕ - Страны" - проходит ')
            continue
        elif num_unique_wo_countries == 0:
            negative.add(topic)
            continue

        # Unique w/o countries and small
        unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_countries_and_small(unique_words)
        if num_unique_wo_small_countries >= 3:
            positive.add(topic)
            topic.method.add('3 "ВСЕ УНИКАЛЬНЫЕ - Страны и Прописные" - проходит ')
            continue

        # Unique FIO
        unique_fio, num_unique_fio = topic.fio(unique_words)
        if num_unique_fio >= 2:
            positive.add(topic)
            topic.method.add('2 "УНИКАЛЬНЫЕ ФИО" - проходит ')
            continue

        # Unique big
        unique_big, num_unique_big = topic.big(unique_words)
        if num_unique_big >= 3:
            positive.add(topic)
            topic.method.add('3 "УНИКАЛЬНЫЕ ЗАГЛАВНЫЕ" - проходит ')
            continue

        # Unique small - already count
        unique_small, num_unique_small = topic.small(unique_words)
        if num_unique_small >= 4:
            positive.add(topic)
            topic.method.add('4 "УНИКАЛЬНЫЕ ПРОПИСНЫЕ" - проходит ')
            continue

        # Unique countries - already count
        unique_countries, num_unique_countries = topic.countries(unique_words)
        if num_unique_countries >= 3:
            positive.add(topic)
            topic.method.add('3 "УНИКАЛЬНЫЕ СТРАНЫ" - проходит ')
            continue

        # Unique IDs
        unique_ids, _ = topic.ids(unique_words)
        if unique_ids:
            positive.add(topic)
            topic.method.add('1 "УНИКАЛЬНЫЕ id" - проходит ')
            continue

    neutral = {topic for topic in topics if topic not in positive and topic not in negative}
    return positive, neutral, negative


def check_neutral_topics(topics):
    positive = set()
    for topic in topics:
        """ 2)	Хотя бы есть среди уникальных 1Загл, 1ФИО, 1 прописн
            3)	Хотя бы есть среди уникальных 1ФИО 1 прописн 1СТ
            4)	Хотя бы есть среди уникальных 1 ФИО 2 прописных
            5)	Хотя бы есть среди уникальных 1 Загл 3 прописных
            6)	Хотя бы есть среди уникальных 2 Загл 1 прописн 1 СТ
            7)	Хотя бы есть 2 ФИО,  среди уникальных 1 ФИО 1 Загл
            8)	Хотя бы есть 2 ФИО,  среди уникальных 1 ФИО 2 СТ
            9)	Хотя бы есть 7 Всех слов, среди уникальных 1 ФИО
            10)	Хотя бы есть 7 Всех слов, среди уникальных 1 Загл
            11)	Хотя бы есть 3 прописных слов, среди уникальных 1 Загл
            12)	 Хотя бы есть 5 Всех слов, 2 прописных, среди уникальных 1 Загл
            13)	Хотя бы есть 1 ФИО, среди уникальных 2 Загл
            14)	Хотя бы есть 4 прописных, среди уникальных 3 прописных
        """
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        # big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        # countries, num_countries = topic.countries(all_words)

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_small_and_countries(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, _ = topic.ids(unique_words)

        # 2
        if num_unique_big >= 1 and num_unique_fio >= 1 and num_unique_small >= 1:
            positive.add(topic)
            topic.method.add('2) уникальных 1Загл, 1ФИО, 1 прописн - проходит ')
            continue

        # 3
        if num_unique_countries >= 1 and num_unique_fio >= 1 and num_unique_small >= 1:
            positive.add(topic)
            topic.method.add('3) уникальных 1ФИО 1 прописн 1СТ - проходит')
            continue

        # 4
        if num_unique_fio >= 1 and num_unique_small >= 2:
            positive.add(topic)
            topic.method.add('4) уникальных 1 ФИО 2 прописных - проходит ')
            continue

        # 5
        if num_unique_big >= 1 and num_unique_small >= 3:
            positive.add(topic)
            topic.method.add('5) уникальных 1 Загл 3 прописных - проходит ')
            continue

        # 6
        if num_unique_big >= 2 and num_unique_small >= 1 and num_unique_countries >= 1:
            positive.add(topic)
            topic.method.add('6) уникальных 2 Загл 1 прописн 1 СТ - проходит ')
            continue

        # 7
        if num_fio >= 2 and num_unique_fio >= 1 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('7) 2 ФИО, среди уникальных 1 ФИО 1 Загл - проходит ')
            continue

        # 8
        if num_fio >= 2 and num_unique_fio >= 1 and num_unique_countries >= 2:
            positive.add(topic)
            topic.method.add('8) 2 ФИО, среди уникальных 1 ФИО 2 СТ - проходит ')
            continue

        # 9
        if num_all_words >= 7 and num_unique_fio >= 1:
            positive.add(topic)
            topic.method.add('9) 7 Всех слов, среди уникальных 1 ФИО - проходит ')
            continue

        # 10
        if num_all_words >= 7 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('10) 7 Всех слов, среди уникальных 1 Загл - проходит ')
            continue

        # 11
        if num_small >= 3 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('11) 3 прописных слов, среди уникальных 1 Загл - проходит ')
            continue

        # 12
        if num_all_words >= 5 and num_small >= 2 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('12) 5 Всех слов, 2 прописных, среди уникальных 1 Загл - проходит ')
            continue

        # 13
        if num_fio >= 1 and num_unique_big >= 2:
            positive.add(topic)
            topic.method.add('13) 1 ФИО, среди уникальных 2 Загл - проходит ')
            continue

        # 14
        if num_small >= 4 and num_unique_small >= 3:
            positive.add(topic)
            topic.method.add('14) 4 прописных, среди уникальных 3 прописных - проходит')
            continue
    return positive


def unite_fio_copy(topics):
    for topic in topics:

        fios1 = set()
        fios2 = set()

        text1 = topic.news[0].all_text_splitted.copy()
        strings_to_check1 = [' '.join(b) for a, b in itertools.groupby(text1, key=lambda x: x[0].isupper() and x.lower() not in STOP_WORDS) if a]
        for k in range(3):
            strings_to_check1 = [word if len(word) > 1 and not word.split()[0][0].islower() else " ".join(word.split()[1:]) for word in strings_to_check1]
            strings_to_check1 = [word if len(word) > 1 and not word.split()[-1][0].islower() else " ".join(word.split()[:-1]) for word in strings_to_check1]
            strings_to_check1 = [word if word.lower() not in STOP_WORDS else "" for word in strings_to_check1]
        strings_to_check1 = [word for word in strings_to_check1 if word]
        print("1", strings_to_check1)

        def split_by_two_words(strings_to_check):
            strings_to_check_copy = strings_to_check.copy()

            for word in strings_to_check:
                word_splitted = word.split()
                by_two = []
                if len(word_splitted) > 2:
                    for i in range(len(word_splitted)-1):
                        by_two.append(word_splitted[i]+" "+word_splitted[i+1])
                if by_two:
                    strings_to_check_copy.remove(word)
                    strings_to_check_copy.extend(by_two)

            return strings_to_check_copy

        strings_to_check1 = split_by_two_words(strings_to_check1)
        print("2", strings_to_check1)
        text2 = topic.news[1].all_text_splitted.copy()
        strings_to_check2 = [' '.join(b) for a, b in itertools.groupby(text2, key=lambda x: x[0].isupper() and x.lower() not in STOP_WORDS or x[0].isupper()) if a]
        for k in range(3):
            strings_to_check2 = [word if len(word) > 1 and not word.split()[0][0].islower() else " ".join(word.split()[1:]) for word in strings_to_check2]
            strings_to_check2 = [word if len(word) > 1 and not word.split()[-1][0].islower() else " ".join(word.split()[:-1]) for word in strings_to_check2]
            strings_to_check2 = [word if word.lower() not in STOP_WORDS else '' for word in strings_to_check2]
        strings_to_check2 = [word for word in strings_to_check2 if word]

        strings_to_check2 = split_by_two_words(strings_to_check2)

        for word1 in strings_to_check1:
            if strings_to_check1.count(word1) >= 2:
                fios1.add(word1)
                continue
            if strings_to_check1.count(word1) >= 1 and strings_to_check2.count(word1) >= 1:
                fios1.add(word1)
                continue
            if any(True if w in word1 else False for w in strings_to_check2):
                fios1.add(word1)
                continue

        for word2 in strings_to_check2:
            if strings_to_check2.count(word2) >= 2:
                fios2.add(word2)
                continue
            if strings_to_check2.count(word2) >= 1 and strings_to_check1.count(word2) >= 1:
                fios2.add(word2)
                continue
            if any(True if w in word2 else False for w in strings_to_check1):
                fios2.add(word2)
                continue

        topic.news[0].all_text.update(set(fios1))
        topic.news[1].all_text.update(set(fios2))

        # to_remove1 = set()
        # to_remove2 = set()
        #
        # for word in topic.news[0].all_text:
        #     if any(True if word in w else False for w in topic.news[0].all_text):
        #         to_remove1.add(word)
        #
        # for word in topic.news[1].all_text:
        #     if any(True if word in w else False for w in topic.news[1].all_text):
        #         to_remove2.add(word)
        #
        # topic.news[0].all_text -= to_remove1
        # topic.news[1].all_text -= to_remove2

        # topic.name = topic.news[0].all_text.intersection(topic.news[1].all_text)
        topic.name = intersection_with_substrings(topic.news[0].all_text, topic.news[1].all_text)
        name = topic.name.copy()

        name = unite_countries_in(name)

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        topic.name = name
        # print(topic.name)
        topic.new_name = topic.name.copy()

    return topics


def unite_entities_copy(topics):
    for topic in topics:

        topic.name = unite_countries_in(topic.name)

        for i in range(2):

            topic.news[i].all_text = unite_countries_in(topic.news[i].all_text)

            debug = False

            if topic.news[i].id == "165" or topic.news[i].id == "107":
                debug = True

            if i == 0:
                j = 1
            else:
                j = 0

            text1 = (topic.news[i].translated['title'] + topic.news[i].translated['lead']
                     + topic.news[i].translated['content'])
            text1_splitted = re.findall(r"[\w']+|[^\s\w]", text1)
            if debug:
                print(text1_splitted)

            text2 = (topic.news[j].translated['title'] + topic.news[j].translated['lead']
                     + topic.news[j].translated['content'])
            text2_splitted = re.findall(r"[\w']+|[^\s\w]", text2)

            to_add = set()
            to_remove = set()

            for ent1 in topic.news[i].all_text:

                for ent2 in topic.news[i].all_text:

                    if ent1 != ent2 and ent1[0].isupper() and (
                            ent1 in topic.news[i].first_words.keys() and topic.news[i].first_words[ent1] or ent1 not in
                            topic.news[i].first_words.keys()):
                        if ent2[0].isupper() and (
                                ent2 in topic.news[i].first_words.keys() and topic.news[i].first_words[ent2] or ent2 not in
                                topic.news[i].first_words.keys()):
                            if ent1 not in TITLES and ent2 not in TITLES and ent1 not in COUNTRIES and ent2 not in COUNTRIES:

                                if debug:
                                    print(ent1)
                                if debug:
                                    print(ent2)

                                previous_word1 = ''
                                previous_word2 = ''
                                next_word1 = ''
                                next_word2 = ''

                                try:
                                    idx1 = text1_splitted.index(ent1)
                                except ValueError:
                                    continue

                                try:
                                    idx2 = text1_splitted.index(ent2)
                                except ValueError:
                                    continue

                                if idx1 > idx2:
                                    words_between = text1_splitted[idx2 + 1:idx1]
                                    if len(words_between) <= 1:

                                        between_str = ' '

                                        for word in words_between:
                                            if word == "-" or word == "'":
                                                between_str += word
                                            elif word.isalpha():
                                                between_str += word
                                                between_str += ' '
                                            else:
                                                break
                                        st = ent2 + between_str + ent1
                                        # print(st)
                                    else:
                                        continue

                                else:
                                    words_between = text1_splitted[idx1 + 1:idx2]
                                    if len(words_between) <= 3:

                                        between_str = ' '

                                        for word in words_between:
                                            if word == "-" or word == "'":
                                                between_str += word
                                            elif word.isalpha():
                                                between_str += word
                                                between_str += ' '
                                            else:
                                                break
                                        st = ent1 + between_str + ent2
                                        # print(st)
                                    else:
                                        continue

                                if ent1 in text2_splitted:

                                    i1 = text2_splitted.index(ent1)

                                    try:
                                        previous_word1 = text2_splitted[i1 - 1]
                                    except IndexError:
                                        previous_word1 = 'a'

                                    try:
                                        next_word1 = text2_splitted[i1 + 1]
                                    except IndexError:
                                        next_word1 = 'a'

                                if ent2 in text2_splitted:

                                    i2 = text2_splitted.index(ent2)

                                    try:
                                        previous_word2 = text2_splitted[i2 - 1]
                                    except IndexError:
                                        previous_word2 = 'a'

                                    try:
                                        next_word2 = text2_splitted[i2 + 1]
                                    except IndexError:
                                        next_word2 = 'a'

                                if text1.count(st) >= 2 or text2.count(st) >= 2:

                                    to_remove.add(ent1)
                                    to_remove.add(ent2)
                                    to_add.add(st)
                                    # print(f"1: {topic.news[i].id} {ent1} {ent2} -> {st} because {text1.count(st)} or {text2.count(st)}")

                                    continue

                                elif st in text1 and st in text2:
                                    to_remove.add(ent1)
                                    to_remove.add(ent2)
                                    to_add.add(st)
                                    # print(f"2: {topic.news[i].id} {ent1} {ent2} -> {st} because {st in text1} and {st in text2}")
                                    continue

                                # elif st in topic.news[0].translated['content'] and ent1 in text:
                                elif len(st.split()) == 2 and st in text1 and ent1 in text2_splitted and \
                                        (previous_word1.islower() or previous_word1 in punctuation or previous_word1 in PUNKTS or previous_word1 in TITLES) \
                                        and (next_word1.islower() or next_word1 in punctuation or next_word1 in PUNKTS or next_word1 in TITLES):
                                    try:
                                        # if text[text.index(ent1)-1][0].islower() and text[text.index(ent1)+1][0].islower():

                                        to_remove.add(ent1)
                                        to_remove.add(ent2)
                                        to_add.add(st)
                                        # print(f"3: {topic.news[i].id} {ent1} {ent2} -> {st} because prev_word {previous_word1} next_word {next_word1}")

                                    except IndexError:
                                        pass
                                # elif st in topic.news[0].translated['content'] and ent2 in text:
                                elif len(st.split()) == 2 and st in text1 and ent2 in text2_splitted and \
                                        (previous_word2.islower() or previous_word2 in punctuation or previous_word2 in PUNKTS or previous_word2 in TITLES) \
                                        and (next_word2.islower() or next_word2 in punctuation or next_word2 in PUNKTS or next_word2 in TITLES):
                                    try:

                                        # if text[text.index(ent2)-1][0].islower() and text[text.index(ent2)+1][0].islower():

                                        to_remove.add(ent1)
                                        to_remove.add(ent2)
                                        to_add.add(st)
                                        # print(f"4: {topic.news[i].id} {ent1} {ent2} -> {st} because prev_word {previous_word2} next_word {next_word2}")
                                    except IndexError:
                                        pass
                                # elif st in text1 and ent2 in text and (previous_word2[0].isupper() or next_word2.isupper()):
                                #     print(5)
                                #     print(st)
                                #     print(previous_word2+ent2+next_word2)
                                #
                                #     ent_dict[ent2] = ' '
                                # elif st in text1 and ent1 in text and (previous_word1[0].isupper() or next_word1.isupper()):
                                #     print(6)
                                #     print(st)
                                #     print(previous_word1 + ent1 + next_word1)
                                #
                                #     ent_dict[ent1] = ' '

            all_text = topic.news[i].all_text

            all_text = (all_text | to_add)-to_remove
            topic.news[i].all_text = all_text

        topic.name = topic.news[0].all_text.intersection(topic.news[1].all_text)
        name = topic.name.copy()



        name = unite_countries_in(name)


        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        topic.name = name
        topic.new_name = topic.name.copy()

        # if any(w for w in topic.name if w[0].islower()):
        #     topic.name = intersect(topic.news[0].description, topic.news[1].description)
        # else:
        #     topic.name = intersect(topic.news[0].named_entities['content'], topic.news[1].named_entities['content'])

    return topics


def unite_entities(topics):
    for topic in topics:

        for i in range(2):

            ent_dict = {}

            if i == 0:
                j = 1
            else:
                j = 0

            for ent1 in topic.news[i].all_text:
                for ent2 in topic.news[i].all_text:
                    if ent1[0].isupper() and (
                            ent1 in topic.news[i].first_words.keys() and topic.news[i].first_words[ent1] or ent1 not in
                            topic.news[i].first_words.keys()):
                        if ent2[0].isupper() and (
                                ent2 in topic.news[i].first_words.keys() and topic.news[i].first_words[
                            ent2] or ent2 not in topic.news[i].first_words.keys()):
                            if ent1 not in TITLES and ent2 not in TITLES:

                                st = ent1 + ' ' + ent2

                                previous_word1 = ''
                                previous_word2 = ''
                                next_word1 = ''
                                next_word2 = ''

                                text2 = (topic.news[j].translated['title'] + topic.news[j].translated['lead'] +
                                         topic.news[j].translated['content'])

                                text = text2.split()
                                text1 = (topic.news[i].translated['title'] + topic.news[i].translated['lead'] +
                                         topic.news[i].translated['content'])

                                if ent1 in text:

                                    i1 = text.index(ent1)

                                    try:
                                        previous_word1 = text[i1 - 1]
                                    except IndexError:
                                        previous_word1 = 'a'

                                    try:
                                        next_word1 = text[i1 + 1]
                                    except IndexError:
                                        next_word1 = 'a'

                                if ent2 in text:

                                    i2 = text.index(ent2)

                                    try:
                                        previous_word2 = text[i2 - 1]
                                    except IndexError:
                                        previous_word2 = 'a'

                                    try:
                                        next_word2 = text[i2 + 1]
                                    except IndexError:
                                        next_word2 = 'a'

                                if text1.count(st) >= 2 or text2.count(st) >= 2:

                                    ent_dict[ent1] = st
                                    ent_dict[ent2] = st
                                    continue

                                elif st in text1 and st in text2:

                                    ent_dict[ent1] = st
                                    ent_dict[ent2] = st
                                    continue

                                # elif st in topic.news[0].translated['content'] and ent1 in text:
                                elif st in text1 and ent1 in text and \
                                        (
                                                previous_word1.islower() or previous_word1 in punctuation or previous_word1 in PUNKTS or previous_word1 in TITLES) \
                                        and (
                                        next_word1.islower() or next_word1 in punctuation or next_word1 in PUNKTS or next_word1 in TITLES):
                                    try:
                                        # if text[text.index(ent1)-1][0].islower() and text[text.index(ent1)+1][0].islower():

                                        ent_dict[ent1] = st
                                        ent_dict[ent2] = st

                                    except IndexError:
                                        pass
                                # elif st in topic.news[0].translated['content'] and ent2 in text:
                                elif st in text1 and ent2 in text and \
                                        (
                                                previous_word2.islower() or previous_word2 in punctuation or previous_word2 in PUNKTS or previous_word2 in TITLES) \
                                        and (
                                        next_word2.islower() or next_word2 in punctuation or next_word2 in PUNKTS or next_word2 in TITLES):
                                    try:

                                        # if text[text.index(ent2)-1][0].islower() and text[text.index(ent2)+1][0].islower():

                                        ent_dict[ent1] = st
                                        ent_dict[ent2] = st
                                    except IndexError:
                                        pass
                                # elif st in text1 and ent2 in text and (previous_word2[0].isupper() or next_word2.isupper()):
                                #     print(5)
                                #     print(st)
                                #     print(previous_word2+ent2+next_word2)
                                #
                                #     ent_dict[ent2] = ' '
                                # elif st in text1 and ent1 in text and (previous_word1[0].isupper() or next_word1.isupper()):
                                #     print(6)
                                #     print(st)
                                #     print(previous_word1 + ent1 + next_word1)
                                #
                                #     ent_dict[ent1] = ' '

            for k in range(2):

                all_text = topic.news[k].all_text.copy()
                for ent in topic.news[k].all_text:
                    if ent in ent_dict.keys() and ent_dict[ent] != ' ':

                        if ent in all_text:
                            all_text.remove(ent)
                            all_text.add(ent_dict[ent])
                    elif ent in ent_dict.keys() and ent_dict[ent] == ' ':

                        if ent in all_text:
                            all_text.remove(ent)

                topic.news[k].all_text = all_text

            # nes_content = topic.news[i].named_entities['content'].copy()
            #
            # for ent in topic.news[i].named_entities['content']:
            #     if ent in ent_dict.keys():
            #         nes_content.remove(ent)
            #         nes_content.add(ent_dict[ent])
            #
            # topic.news[i].named_entities['content'] = nes_content
            #
            # nes_descr = topic.news[i].description.copy()
            #
            # for ent in topic.news[i].description:
            #     if ent in ent_dict.keys():
            #         nes_descr.remove(ent)
            #         nes_descr.add(ent_dict[ent])
            #
            # topic.news[i].description = nes_descr
            #
            # topic.news[i].all_text = nes_descr.union(nes_content)

        topic.name = topic.news[0].all_text.intersection(topic.news[1].all_text)
        name = topic.name.copy()

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        name = unite_countries_in(name)

        topic.name = name
        topic.new_name = name.copy()
        # if any(w for w in topic.name if w[0].islower()):
        #     topic.name = intersect(topic.news[0].description, topic.news[1].description)
        # else:
        #     topic.name = intersect(topic.news[0].named_entities['content'], topic.news[1].named_entities['content'])

    return topics


def split_into_single(dataset):
    new_dataset = set()
    for d in dataset:
        for s in d.split(' '):
            if not all(True if w.isupper() else False for w in s):
                new_dataset.add(s)
            else:
                new_dataset.add(d)
    return new_dataset


def delete_without_lower(topics):
    new_topics = []
    for topic in topics:
        if not all(True if w[0].isupper() or w.isdigit() else False for w in topic.name):
            new_topics.append(topic)

    return new_topics


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


def check_topics(topics):
    new_topics = []
    for topic in topics:

        if count_not_countries(topic.name) >= 2 and count_countries(topic.name) >= 1:
            new_topics.append(topic)
    return new_topics


if __name__ == '__main__':
    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    time = datetime.now()

    # c_descr = CorpusD(db, table)
    # c_descr.find_topics()
    # write_topics("Descriptions.xlsx", c_descr.topics)
    #
    # c_descr.delete_small()
    # c_descr.check_unique()
    # c_descr.topics = unite_entities(c_descr.topics)
    # c_descr.topics = [t for t in c_descr.topics if t.isvalid()]
    #
    # c_content = CorpusC(db, table)
    # c_content.find_topics()
    # write_topics("Texts.xlsx", c_content.topics)
    #
    # c_content.delete_small()
    # c_content.check_unique()
    # c_content.topics = unite_entities(c_content.topics)
    # c_content.topics = [t for t in c_content.topics if t.isvalid()]
    #
    # all_topics = c_descr.topics
    # all_topics.extend(c_content.topics)

    corpus = Corpus(db, table)
    corpus.find_topics()
    corpus.delete_small()
    write_topics("0.xlsx", corpus.topics)
    print(0, len(corpus.topics))

    corpus.topics = unite_fio(corpus.topics)
    write_topics("1.xlsx", corpus.topics)
    print(1, len(corpus.topics))

    corpus.topics = check_topics(corpus.topics)
    write_topics("2.xlsx", corpus.topics)
    initial_topics = corpus.topics.copy()
    print(2, len(corpus.topics))

    corpus.check_unique()
    write_topics("3.xlsx", corpus.topics)
    print(3, len(corpus.topics))

    corpus.topics = add_words_to_topics(corpus.topics)
    write_topics("4.xlsx", corpus.topics)
    print(4, len(corpus.topics))

    pos, neu, neg = filter_topics(corpus.topics)
    write_topics("5-Positive.xlsx", pos)
    write_topics("5-Neutral.xlsx", neu)
    write_topics("5-Negative.xlsx", neg)
    print(5, len(pos), len(neu), len(neg))

    pos_1 = check_neutral_topics(neu)
    topics = pos
    topics.update(pos_1)

    write_topics("6.xlsx", topics)
    print(6, len(topics))

    united_topics = set()

    for topic1 in initial_topics:
        for topic2 in topics:
            new_name = topic1.name.intersection(topic2.name)
            if count_countries(new_name) >= 1 and count_not_countries(new_name) >= 2:
                news_list = topic1.news
                news_list.extend(topic2.news)
                new_topic = Topic(new_name, news_list)
                pos, _, _ = filter_topics([new_topic])
                if pos:
                    united_topics.add(new_topic)

    write_topics("7.xlsx", united_topics)
    print(7, len(united_topics))

    print(datetime.now() - time)

"""
    write_topics("0.xlsx", all_topics)

    all_topics = extend_topic_names(all_topics)

    # all_topics = unite_entities(all_topics)
    # write_topics("0.xlsx", all_topics)

    all_topics = redefine_unique(all_topics)
    write_topics("1.xlsx", all_topics)

    all_topics = find_objects(all_topics)
    write_topics("2.xlsx", all_topics)

    all_topics = delete_without_lower(all_topics)
    write_topics("3.xlsx", all_topics)

    all_topics = assign_news(all_topics, c_descr.data)
    for topic in all_topics:
        topic.news = delete_dupl_from_news(topic.news)
    write_topics("4.xlsx", all_topics)

    i = 0
    topics_copy = set()
    while len(topics_copy) != len(all_topics):
        topics_copy = all_topics.copy()
        all_topics = similar(all_topics)
        for topic in all_topics:
            topic.news = delete_dupl_from_news(topic.news)
        write_topics(f"{i+5}.xlsx", all_topics)
        i += 1

    write_topics(f"{i+5}.xlsx", all_topics)

    
    """
