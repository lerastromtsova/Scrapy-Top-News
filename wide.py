from corpus import count_countries, count_not_countries
from corpus import Corpus, Topic, intersect, intersect_with_two
from xl_stats import write_topics, write_topics_with_subtopics
from datetime import datetime
from descr import iscountry
from math import ceil
from text_processing.preprocess import PUNKTS
from string import punctuation
import re
from document import COUNTRIES
import itertools
from draw_graph import draw_graph
from text_processing.preprocess import STOP_WORDS, check_first_entities, unite_countries_in, unite_countries_in_topic_names
from copy import deepcopy


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
    topics = list(topics)
    for i, t in enumerate(topics):
        if t:
            others = [to for to in topics if to is not None]
            others = [to for to in others if t != to]
            ids = {new.id for new in t.news}
            for o in others:
                if o:
                    other_ids = {n.id for n in o.news}
                    if ids == other_ids:
                        o.name |= t.name
                        topics[i] = None
    topics = {t for t in topics if t is not None}
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


def add_words_to_topics(topics):

    for topic in topics:
        sent_dict = dict.fromkeys(list(range(len(topic.news))))

        for word in topic.new_name:

            common_words = set()

            for i, new in enumerate(topic.news):
                sent_dict[i] = {word: {w for sent in new.sentences for w in sent.split() if word in sent}}

            for i, new in enumerate(topic.news):
                common_words &= sent_dict[i][word]

            topic.name.update(common_words)

    return topics


def sublist(l1, l2):
    s1 = ''.join(map(str, l1))
    s2 = ''.join(map(str, l2))
    return re.search(s1, s2)


def count_similar(word, words_list):
    c = 0
    for w in words_list:
        if w == word:
            c += 1
            continue
        if sublist(word, w) and len(w.split()) > 1:
            c += 1
    return c


def get_other(number):
    if number == 1:
        return 0
    return 1


def unite_fio(topics):
    STOP_WORDS.append("house")
    for topic in topics:

        countries_in_name, _ = topic.countries(topic.name)
        small_in_name, _ = topic.small(topic.name)
        ids_in_name, _ = topic.ids(topic.name)
        # big_in_name, _ = topic.big(topic.name)
        # big_to_leave = {w for w in big_in_name if w in topic.frequent}

        fios = {}
        strings_to_check = {}
        check_len_1 = {}
        check_len_2 = {}
        check_len_4_all_big = {}
        check_len_4_some_small = {}
        to_remove = {}
        debug = False

        # if topic.news[0].id == 165 and topic.news[1].id == 125 or topic.news[0].id == 125 and topic.news[1].id == 16:
        #     debug = True

        to_remove[0] = set()
        to_remove[1] = set()

        fios[0] = set()
        fios[1] = set()

        strings_to_check[0] = topic.news[0].uppercase_sequences
        strings_to_check[0] = unite_countries_in(strings_to_check[0])
        strings_to_check[0] = [w for w in strings_to_check[0] if not iscountry(w)]

        strings_to_check[1] = topic.news[1].uppercase_sequences
        strings_to_check[1] = unite_countries_in(strings_to_check[1])
        strings_to_check[1] = [w for w in strings_to_check[1] if not iscountry(w)]

        if debug:
            print("ID1", topic.news[0].id)
            print(1, strings_to_check[0])
            print("ID2", topic.news[1].id)
            print(2, strings_to_check[1])

        if debug:
            print(topic.name)
            print(countries_in_name)

        # big_in_name = [w for w in topic.name if w in strings_to_check[0] or w in strings_to_check[1]]

        for word in topic.name:
            words_containing1 = {w for w in strings_to_check[0] if word in w and w != word}
            words_containing2 = {w for w in strings_to_check[1] if word in w and w != word}
            if not words_containing1 or not words_containing2:
                fios[0].add(word)
                fios[1].add(word)
                to_remove[0].add(word)
                to_remove[1].add(word)
            if words_containing1 == words_containing2 and words_containing1:
                elem1 = words_containing1.pop()
                elem2 = words_containing2.pop()
                fios[0].add(elem1)
                fios[1].add(elem2)
                to_remove[0].add(elem1)
                to_remove[1].add(elem2)

        strings_to_check[0] = [w for w in strings_to_check[0] if w not in to_remove[0]]
        strings_to_check[1] = [w for w in strings_to_check[1] if w not in to_remove[1]]

        check_len_1[0] = [s for s in strings_to_check[0] if len(s.split()) == 1]
        check_len_1[1] = [s for s in strings_to_check[1] if len(s.split()) == 1]

        check_len_2[0] = [s for s in strings_to_check[0] if len(s.split()) == 2]
        check_len_2[1] = [s for s in strings_to_check[1] if len(s.split()) == 2]

        check_len_4_all_big[0] = [s for s in strings_to_check[0] if len(s.split()) > 2 and s[0].isupper()]
        check_len_4_all_big[1] = [s for s in strings_to_check[1] if len(s.split()) > 2 and s[0].isupper()]

        check_len_4_some_small[0] = [s for s in strings_to_check[0] if
                                     len(s.split()) > 2 and any(w for w in s.split() if w.islower())]
        check_len_4_some_small[1] = [s for s in strings_to_check[1] if
                                     len(s.split()) > 2 and any(w for w in s.split() if w.islower())]

        """ Check if some word is repeated twice in one news or once in each news """

        for i in range(2):
            j = get_other(i)
            for word in strings_to_check[i]:
                if len(word.split()) >= 2:
                    if strings_to_check[i].count(word) >= 2 or strings_to_check[j].count(word) >= 2:
                        fios[i].add(word)
                        if debug:
                            print("Word is repeated twice | ", word)
                    elif strings_to_check[i].count(word) >= 1 and strings_to_check[j].count(word) >= 1:
                        fios[i].add(word)
                        if debug:
                            print("Word is repeated once in each | ", word)

        """ Checking multi-words fio (all big letters)"""
        continuei = ContinueI()

        for i in range(2):
            j = get_other(i)
            for word in check_len_4_all_big[i]:
                one_last = ' '.join(word.split()[-1:])
                two_last = ' '.join(word.split()[-2:])
                two_middle = ' '.join(word.split()[1:3])
                two_first = ' '.join(word.split()[:2])
                three_last = ' '.join(word.split()[-3:])
                three_first = ' '.join(word.split()[:3])

                if debug:
                    print(one_last)
                    print(two_last)
                    print(two_middle)
                    print(two_first)

                try:

                    for w in check_len_4_all_big[i]:
                        if w != word:
                            if w == three_last:
                                if debug:
                                    print(f"Replaced word with length 4 {word} with {three_last}")
                                fios[i].add(three_last)
                                raise continuei
                            elif w == three_first:
                                if debug:
                                    print(f"Replaced word with length 4 {word} with {three_last}")
                                fios[i].add(three_first)
                                raise continuei

                    for w in check_len_4_all_big[j]:
                        if w != word:
                            if w == three_last:
                                if debug:
                                    print(f"Replaced word with length 4 {word} with {three_last}")
                                fios[i].add(three_last)
                                fios[j].add(three_last)
                                raise continuei
                            elif w == three_first:
                                if debug:
                                    print(f"Replaced word with length 4 {word} with {three_last}")
                                fios[i].add(three_first)
                                fios[j].add(three_first)
                                raise continuei

                    for w in check_len_2[i]:
                        if w == two_last:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {two_last}")
                            fios[i].add(two_last)
                            raise continuei
                        elif w == two_middle:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {two_last}")
                            fios[i].add(two_middle)
                            raise continuei
                        elif w == two_first:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {two_last}")
                            fios[i].add(two_first)
                            raise continuei

                    for w in check_len_2[j]:
                        if w == two_last:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {two_last}")
                            fios[i].add(two_last)
                            fios[j].add(two_last)
                            raise continuei
                        elif w == two_middle:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {two_last}")
                            fios[i].add(two_middle)
                            fios[j].add(two_middle)
                            raise continuei
                        elif w == two_first:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {two_last}")
                            fios[i].add(two_first)
                            fios[j].add(two_first)
                            raise continuei

                    for w in check_len_1[i]:
                        if w == one_last:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {one_last}")
                            fios[i].add(one_last)
                            raise continuei

                    for w in check_len_1[j]:
                        if w == one_last:
                            if debug:
                                print(f"Replaced word with length 4 {word} with {one_last}")
                            fios[i].add(one_last)
                            fios[j].add(one_last)
                            raise continuei

                except ContinueI:
                    continue

        # for word in strings_to_check1:
        #     if len(word.split()) >= 2:
        #         if count_similar(word, strings_to_check1) >= 2:
        #             fios.add(word)
        #         if count_similar(word, strings_to_check2) >= 1:
        #             fios.add(word)
        #
        # for word in strings_to_check2:
        #     if len(word.split()) >= 2:
        #         if count_similar(word, strings_to_check2) >= 2:
        #             fios.add(word)
        #         if count_similar(word, strings_to_check1) >= 1:
        #             fios.add(word)

        # common_strings = set(strings_to_check1).intersection(set(strings_to_check2))

        """ Checking multi-words fio (some small letters)"""
        for i in range(2):
            j = get_other(i)
            for word in check_len_4_some_small[i]:
                all_big = ' '.join([w for w in word.split() if w[0].isupper()])
                for w in check_len_4_all_big[i]:
                    if all_big == w:
                        if debug:
                            print("Some words were the same", word, "to", all_big)
                        fios[i].add(all_big)
                for w in check_len_4_all_big[j]:
                    if all_big == w:
                        if debug:
                            print("Some words were the same", word, "to", all_big)
                        fios[j].add(all_big)

                for w in check_len_2[i]:
                    if all_big == w:
                        if debug:
                            print("Some words were the same", word, "to", all_big)
                        fios[i].add(all_big)
                for w in check_len_2[j]:
                    if all_big == w:
                        if debug:
                            print("Some words were the same", word, "to", all_big)
                        fios[j].add(all_big)

        """ Checking two-words fio """

        for i in range(2):
            j = get_other(i)
            for word in check_len_2[i]:
                last_word = word.split()[-1]
                if last_word in check_len_1[i] or last_word in check_len_1[j]:
                    words_containing1 = {w for w in strings_to_check[i] if last_word == w.split()[-1] and last_word != w}
                    words_containing2 = {w for w in strings_to_check[j] if last_word == w.split()[-1] and last_word != w}
                    if debug:
                        print(words_containing1)
                        print(words_containing2)
                    c1 = len(words_containing1)
                    c2 = len(words_containing2)
                    if c1 > 1 or c2 > 1 or (c1 + c2 >= 2 and words_containing1 != words_containing2):
                        # fios[i].add(last_word)
                        if debug:
                            print("Word is in different FIOs | ", last_word)
                        continue
                    else:
                        fios[i].add(word)
                        # fios[j].add(word)
                        if debug:
                            print("Word is not in different FIOs | ", word)
                        continue

        if debug:
            print("FIO1", fios[0])
            print("FIO2", fios[1])
        # print("ID2", topic.news[1].id)

        # print(topic.name)

        topic.news[0].all_text.update(fios[0])
        topic.news[1].all_text.update(fios[1])

        topic.name = set(countries_in_name)
        topic.name.update(set(small_in_name))
        topic.name.update(set(ids_in_name))
        # topic.name.update(set(big_in_name))

        common_fios = intersect(fios[0], fios[1])
        topic.name.update(common_fios)

        numbers = topic.news[0].numbers.intersection(topic.news[1].numbers)
        topic.all_numbers = numbers

        name = topic.name.copy()

        for word in topic.name:
            if any(True if word in w or word.upper() in w else False for w in topic.name - {word}):
                name -= {word}

        topic.name = name
        topic.name = unite_countries_in(topic.name)
        topic.name = unite_countries_in_topic_names(topic.name)
        topic.name = {w for w in topic.name if w.lower() not in STOP_WORDS}
        topic.new_name = topic.name.copy()
        topic.frequent = topic.most_frequent()

    return topics


def unite_fio1(topics):
    for topic in topics:

        fios = set()
        # text1 = topic.news[0].all_text_splitted.copy()
        # text1 = [w for w in text1 if len(w) > 1]
        # # print(text1)
        # strings_to_check1 = find_all_uppercase_sequences(text1)
        # strings_to_check2 = trim_words(strings_to_check2)

        strings_to_check1 = topic.news[0].uppercase_sequences
        strings_to_check2 = topic.news[1].uppercase_sequences

        print(1, strings_to_check1)
        print(2, strings_to_check2)

        common_strings = intersect_with_two(strings_to_check1, strings_to_check2)
        print(3, common_strings)
        # print(1, strings_to_check1)
        # print(2, strings_to_check2)
        # print(3, common_strings)

        fios.update(common_strings)

        short_strings1 = {w for w in strings_to_check1 if len(w.split()) <= 2}

        short_strings2 = {w for w in strings_to_check2 if len(w.split()) <= 2}
        print("short1", short_strings1)
        print("short2", short_strings2)

        for word1 in short_strings1:
            for word2 in short_strings2:
                if len(word2.split()) >= 2:
                    if word1 == word2.split()[-1]:
                        if any(w for w in strings_to_check1 if word1 == w.split()[-1] and word1 != w and w != word2)\
                                and any(w for w in strings_to_check2 if word1 == w.split()[-1] and word1 != w and w != word2):  # if word1 consists in any fios in sequences1 and 2
                            pass
                        else:
                            print(word2)
                            fios.add(word2)
                if len(word1.split()) >= 2:
                    if word2 == word1.split()[-1]:
                        if any(w for w in strings_to_check2 if word2 == w.split()[-1] and word2 != w and w != word1)\
                                and any(w for w in strings_to_check1 if word2 == w.split()[-1] and word2 != w and w != word1):
                            pass
                        else:
                            print(word1)
                            fios.add(word1)

        topic.news[0].all_text.update(set(fios))
        topic.news[1].all_text.update(set(fios))

        topic.name = intersect(topic.news[0].all_text, topic.news[1].all_text)
        print("Name", topic.name)

        # to_remove = set()
        #
        # for str1 in strings_to_check1:
        #     for str2 in strings_to_check2:
        #         if str1.split()[0] == str2.split()[0]:
        #             if str1 != str2:
        #                 if str1.split()[0] in topic.name:
        #                     to_remove.add(str1.split()[0])
        #
        # topic.name -= to_remove

        name = topic.name.copy()

        name = unite_countries_in(name)

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}
                print(word)

        topic.name = name

        short_to_check = {w for w in name if len(w.split()) == 1 and w not in COUNTRIES and w[0].isupper()}

        long = name - short_to_check

        checked_entities = check_first_entities(short_to_check)
        checked_lower = {w for w in checked_entities.keys() if not checked_entities[w]}
        checked_upper = {w for w in checked_entities.keys() if checked_entities[w]}

        name = long | checked_upper

        name = name | checked_lower

        topic.name = name

        to_remove = set()

        for word in topic.name:

            try:
                words1_containing = {w for w in strings_to_check1 if word == w.split()[-2] or word == w.split()[-2]+"s" and word != w}
            except IndexError:
                words1_containing = {w for w in strings_to_check1 if word == w.split()[0] or word == w.split()[0]+"s" and word != w}
            try:
                words2_containing = {w for w in strings_to_check2 if word == w.split()[-2] or word == w.split()[-2]+"s" and word != w}
            except IndexError:
                words2_containing = {w for w in strings_to_check2 if word == w.split()[0] or word == w.split()[0]+"s" and word != w}

            if words1_containing and words2_containing and not words1_containing.intersection(words2_containing):
                to_remove.add(word)

        name -= to_remove
        topic.name = name
        
        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        topic.name = name
        # print(topic.name)
        # print("\n")
        topic.new_name = topic.name.copy()
        # print(topic.name)

    return topics


def filter_topics(topics):

    positive = set()
    for topic in topics:

        # All words
        all_words, num_all_words = topic.all_words(topic.name)
        # if num_all_words >= 9:
        #     positive.add(topic)
        #     topic.method.add('9 "ВСЕ СЛОВА" - проходит ')
        #     continue
        # elif num_all_words <= 1:
        #     negative.add(topic)
        #     continue

        # All w/o countries
        all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # if num_all_wo_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ СЛОВА – Страны" - проходит')
        #     continue
        # elif num_all_wo_countries <= 1:
        #     negative.add(topic)
        #     continue

        # All w/o small & countries
        all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_countries_and_small(all_words)
        # if num_all_wo_small_and_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ СЛОВА - Прописные и Страны" - проходит ')
        #     continue

        # FIO
        fio, num_fio = topic.fio(all_words)
        # if num_fio >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "ФИО" - проходит ')
        #     continue

        # Big letter
        big, num_big = topic.big(all_words)
        # if num_big >= 4:
        #     positive.add(topic)
        #     topic.method.add('4 "ЗАГЛАВНЫЕ" - проходит ')
        #     continue

        # Small - already count
        small, num_small = topic.small(all_words)
        # if num_small >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ПРОПИСНЫЕ" - проходит ')
        #     continue

        # Countries - already count
        countries, num_countries = topic.countries(all_words)
        # if num_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "СТРАНЫ" - проходит ')
        #     continue

        # All unique
        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # if num_unique_words >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ УНИКАЛЬНЫЕ" - проходит ')
        #     continue
        # elif num_unique_words == 0:
        #     negative.add(topic)
        #     continue

        # Unique w/o countries
        unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # if num_unique_wo_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ УНИКАЛЬНЫЕ - Страны" - проходит ')
        #     continue
        # elif num_unique_wo_countries == 0:
        #     negative.add(topic)
        #     continue

        # Unique w/o countries and small
        unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_countries_and_small(unique_words)
        # if num_unique_wo_small_countries >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "ВСЕ УНИКАЛЬНЫЕ - Страны и Прописные" - проходит ')
        #     continue

        # Unique FIO
        unique_fio, num_unique_fio = topic.fio(unique_words)
        # if num_unique_fio >= 2:
        #     positive.add(topic)
        #     topic.method.add('2 "УНИКАЛЬНЫЕ ФИО" - проходит ')
        #     continue

        # Unique big
        unique_big, num_unique_big = topic.big(unique_words)
        # if num_unique_big >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "УНИКАЛЬНЫЕ ЗАГЛАВНЫЕ" - проходит ')
        #     continue

        # Unique small - already count
        unique_small, num_unique_small = topic.small(unique_words)
        # if num_unique_small >= 4:
        #     positive.add(topic)
        #     topic.method.add('4 "УНИКАЛЬНЫЕ ПРОПИСНЫЕ" - проходит ')
        #     continue

        # Unique countries - already count
        unique_countries, num_unique_countries = topic.countries(unique_words)
        # if num_unique_countries >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "УНИКАЛЬНЫЕ СТРАНЫ" - проходит ')
        #     continue

        # Unique IDs
        unique_ids, _ = topic.ids(unique_words)
        # if unique_ids:
        #     positive.add(topic)
        #     topic.method.add('1 "УНИКАЛЬНЫЕ id" - проходит ')
        #     continue

        # 1) 1 уФИО + 2 ФИО
        frequent = topic.most_frequent()
        num_frequent = len(frequent)

        if len(frequent) >= 8:
            frequent_50 = frequent[:ceil(len(frequent) / 2)]
        elif 4 <= len(frequent) <= 8:
            frequent_50 = frequent[:4]
        else:
            frequent_50 = frequent[:len(frequent)]

        num_frequent_50 = len(frequent_50)

        # 1) 1 уФИО + 2 ФИО

        if num_unique_fio >= 1 and num_fio >= 2 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.1) уФИО + 2 ФИО')
            # continue

        # 2) 1 уФИО + 1 оЗагл
        if num_unique_fio >= 1 and num_big >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 2 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.2) 1 уФИО + 1 оЗагл')
            # continue

        # 3) 1 уФИО + 1 оПроп
        if num_unique_fio >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 3 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('.3) 1 уФИО + 1 оПроп')
            # continue

        # 4) 1 уЗагл + 1 оФИО
        if num_unique_big >= 1 and num_fio >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 2 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.4) 1 уЗагл + 1 оФИО')
            # continue

        # 5) 1 уЗагл + 2 оЗагл
        if num_unique_big >= 1 and num_big >= 2 and num_countries >= 1 and (
                num_unique_fio >= 1 or num_big >= 3 or num_unique_small >= 1 or num_unique_countries >= 2):
            positive.add(topic)
            topic.method.add('.5) 1 уЗагл + 2 оЗагл')
            # continue

        # 6) 1 уЗагл + 1 оМал
        if num_unique_big >= 1 and num_small >= 1 and num_countries >= 1 and (
                num_unique_fio >= 1 or num_unique_big >= 2 or num_unique_small >= 2 or num_unique_countries >= 2):
            positive.add(topic)
            topic.method.add('.6) 1 уЗагл + 1 оФИО')
            # continue

        # 7) 1 уЗагл + 2 оСтр
        if num_unique_big >= 1 and num_countries >= 3 and (
                num_unique_fio >= 1 or num_unique_big >= 2 or num_unique_small >= 1 or num_unique_countries >= 1):
            positive.add(topic)
            topic.method.add('.7) 1 уЗагл + 3 оСтр')
            # continue

        # 8) 1 уПроп + 2 оФИО
        if num_unique_small >= 1 and num_fio >= 2 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.8) 1 уПроп + 2 оФИО')
            # continue

        # 9) 1 уПроп + 2 оЗагл
        if num_unique_small >= 1 and num_big >= 2 and num_countries >= 1 and (
                num_unique_fio >= 1 or num_unique_big >= 1 or num_unique_small >= 2 or num_unique_countries >= 2):
            positive.add(topic)
            topic.method.add('.9) 1 уПроп + 2 оЗагл')
            # continue

        # 10) 4 уПроп
        if num_unique_small >= 4 and num_countries >= 1 and (num_fio >= 1 or num_big >= 1 or num_small >= 5 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('10) 4 уПроп ')
            # continue

        # 11) 3 оФИО
        if num_fio >= 3 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('11) 3 оФИО')
            # continue

        # 12) 1 оФИО + 2 оЗагл
        if num_fio >= 1 and num_big >= 2 and num_countries >= 1 and (num_fio >= 2 or num_big >= 3 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('12) 1 оФИО + 2 оЗагл')
            # continue

        # 13) 1 оФИО + 2 оПроп
        if num_fio >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 4 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('13) 1 оФИО + 2 оПроп')
            # continue

        # 14) 2 уФИО
        if num_unique_fio >= 2 and num_countries >= 1 and (num_fio >= 3 or num_big >= 1 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('14) 2 уФИО ')
            # continue

        # 15) 3 уПроп + 1 оФИО
        if num_unique_small >= 3 and num_fio >= 1 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('15) 3 уПроп + 1 оФИО')
            # continue

        # 16) 4 оЗагл
        if num_unique_big >= 4 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('16) 4 оЗагл')
            # continue

        # 17) 1 оЗагл + 2 оПроп
        if num_big >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 2 or num_small >= 4 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('17) 1 оЗагл + 2 оПроп')
            # continue

        # 18) 3 уЗагл
        if num_unique_big >= 3 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('18) 3 уЗагл')
            # continue

        # 19) 3 оЗагл + 1 оПроп
        if num_big >= 3 and num_small >= 1 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 4 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('19) 3 оЗагл + 1 оПроп')
            # continue

        # 20) 5 оСтран
        if num_countries >= 5 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('20) 5 оСтран')
            # continue

        # 21) 2 уПроп + 1 оЗагл
        if num_unique_small >= 2 and num_big >= 1 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 2 or num_small >= 3 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('21) 2 уПроп + 1 оЗагл')
            # continue

        # 22) 1 уФИО + 1 уПроп
        if num_unique_fio >= 1 and num_unique_small >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('22) 1 уЗагл + 1 уПроп')
            # continue

        # 23) 4 уПроп
        if num_unique_small >= 4 and num_countries >= 1 and (num_fio >= 1 or num_big >= 1 or num_small >= 5 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('23) 4 уПроп')
            # continue

        # 24) 4 оСтран
        if num_countries >= 5 and (num_fio >= 1 or num_big >= 1 or num_small >= 1 or num_countries >= 6):
            positive.add(topic)
            topic.method.add('24) 4 оСтран')
            # continue

        # 25) 1 уФИО + 2 уСтран
        if num_unique_fio >= 1 and num_unique_countries >= 2:
            positive.add(topic)
            topic.method.add('25) 1 уФИО + 2 уСтран')
            # continue

        # 26) 1 упроп + 1 уПроп
        if num_unique_small >= 1 and num_unique_countries >= 2 and (
                num_fio >= 1 or num_big >= 1 or num_small >= 2 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('26) 1 упроп + 1 уПроп')
            # continue

        # 27) 3 уСтр
        if num_unique_countries >= 3 and (num_fio >= 1 or num_big >= 1 or num_small >= 1 or num_countries >= 4):
            positive.add(topic)
            topic.method.add('27) 3 уСтр')
            # continue

        # 28) 1 уМал + 2 оМал + 1 оФИО
        if num_unique_small >= 1 and num_small >= 2 and num_fio >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 3 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('27) 1 уМал + 2 оМал + 1 оФИО')
            # continue

    negative = {topic for topic in topics if topic not in positive}
    return positive, negative


def last_check_topics(topics):
    positive = set()
    negative = set()
    for topic in topics:

        topic.frequent = topic.most_frequent()

        if len(topic.frequent) >= 8:
            freq_50 = topic.frequent[:ceil(len(topic.frequent) / 2)]
        elif 4 <= len(topic.frequent) <= 8:
            freq_50 = topic.frequent[:4]
        else:
            freq_50 = topic.frequent[:len(topic.frequent)]

        if len(freq_50) >= 3:
            positive.add(topic)
        elif len(freq_50) >= 2 and len(topic.new_name) >= 1 and count_countries(topic.name) >= 1:
            positive.add(topic)
    negative = {t for t in topics if t not in positive}
    return positive, negative


def check_neutral_topics_copy(topics):
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
            15) 1 ФИО, 3 прописных - проходит 
            16) 2 Загл, 2 прописных - проходит
            17) 1 прописное, среди уникальных 2 Загл - проходит 
        """
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
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

        # 15
        if num_fio >= 1 and num_small >= 3:
            positive.add(topic)
            topic.method.add('15) 1 ФИО, 3 прописных - проходит ')
            continue

        # 16
        if num_big >= 2 and num_small >= 2:
            positive.add(topic)
            topic.method.add('16) 2 Загл, 2 прописных - проходит ')
            continue

        # 17
        if num_small >= 1 and num_unique_big >= 2:
            positive.add(topic)
            topic.method.add('17) 1 прописное, среди уникальных 2 Загл - проходит ')
            continue

    return positive


def check_neutral_topics(topics, coefficients):
    positive = set()
    for topic in topics:
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        ids, num_ids = topic.ids(all_words)
        countries, num_countries = topic.countries(all_words)

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_small_and_countries(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, num_unique_ids = topic.ids(unique_words)

        result = 0

        result += num_fio * coefficients['fio']
        result += num_big * coefficients['big']
        result += num_small * coefficients['small']
        result += num_ids * coefficients['ids']
        if num_countries >= 2:
            result += num_countries * coefficients['countries']

        result += num_unique_fio * coefficients['ufio']
        result += num_unique_big * coefficients['ubig']
        result += num_unique_small * coefficients['usmall']
        result += num_unique_ids * coefficients['uids']
        result += num_unique_countries * coefficients['ucountries']

        if result >= 1:
            topic.result = result
            positive.add(topic)

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


def delete_subtopics(topics):
    to_remove = set()
    for topic in topics:
        others = [t for t in topics if t != topic]
        topic_ids = {n.id for n in topic.news}

        for ot in others:
            ot_ids = {n.id for n in ot.news}
            if ot_ids.issubset(topic_ids) and ot_ids != topic_ids:
                to_remove.add(ot)

    topics = [t for t in topics if t not in to_remove]
    return topics


def clean_topic_name(name):
    name = {w for w in name if not any(word for word in name-{w} if w.lower() in word.lower())}
    return name


class ContinueI(Exception):
    pass


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


def add_news(topics, data):
    for topic in topics:
        for new in data:
            if new not in topic.news:
                new_name = unite_news_text_and_topic_name(new.all_text, topic.name)
                new_unique = unite_news_text_and_topic_name(new.all_text, topic.new_name)

                if new_unique:
                    if count_countries(new_name) >= 1 and count_not_countries(new_name) >= 2:
                            news_list = topic.news.copy()
                            news_list.append(new)
                            new.all_text = new.description
                            new.all_text.update(new.tokens['content'])
                            new_topic = Topic(new_name, news_list)
                            new_topic.new_name = topic.name
                            t, _ = filter_topics([new_topic])
                            if t:
                                topic.methods_for_news[new.id] = new_topic.method
                                topic.news.append(new)

        topic.news = delete_dupl_from_news(topic.news)
    return topics


if __name__ == '__main__':
    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    time = datetime.now()

    corpus = Corpus(db, table)
    corpus.find_topics()
    corpus.delete_small()
    write_topics(f"{db}-0.xlsx", corpus.topics)
    print(0, len(corpus.topics))

    corpus.topics = unite_fio(corpus.topics)
    write_topics(f"{db}-1.xlsx", corpus.topics)
    print(1, len(corpus.topics))

    corpus.topics = check_topics(corpus.topics)
    write_topics(f"{db}-2.xlsx", corpus.topics)
    # initial_topics = corpus.topics.copy()
    print(2, len(corpus.topics))

    corpus.check_unique()
    write_topics(f"{db}-3.xlsx", corpus.topics)
    print(3, len(corpus.topics))


    for topic in corpus.topics:
        topic.name = clean_topic_name(topic.name)
        topic.new_name = clean_topic_name(topic.new_name)

    corpus.topics, neg = filter_topics(corpus.topics)

    write_topics(f"{db}-5-прошли.xlsx", corpus.topics)

    write_topics(f"{db}-5-не прошли.xlsx", neg)
    print(5, len(corpus.topics))

    united_topics = set()

    corpus.topics = add_news(corpus.topics, corpus.data)



    corpus.topics = delete_duplicates(corpus.topics)

    write_topics(f"{db}-6.xlsx", corpus. topics)

    print(6, len(corpus.topics))

    corpus.topics = sorted(corpus.topics, key=lambda x: -len(x.name))

    for i, topic in enumerate(corpus.topics):
        if topic:
            topic.subtopics = set()
            others = [t for t in corpus.topics if t and set(t.news) != set(topic.news)]
            similar = {}
            for ot in others:
                if ot:
                    new_name = unite_news_text_and_topic_name(topic.name, ot.name)
                    new_unique = unite_news_text_and_topic_name(topic.new_name, ot.name)
                    news_list = list(set(topic.news).union(set(ot.news)))

                    new_topic = Topic(new_name, news_list)
                    new_topic.new_name = new_unique
                    t, _ = filter_topics([new_topic])
                    if t:
                        similar[ot] = t.pop().method

            if similar:
                topic_copy = Topic(topic.name, topic.news)
                topic_copy.new_name = topic.new_name
                topic.subtopics.add(topic_copy)

                for s, m in similar.items():
                    topic.subtopics.add(s)
                    s.method = m
                    topic.news.extend(s.news)

                topic.news = delete_dupl_from_news(topic.news)

    corpus.topics = [t for t in corpus.topics if t]

    corpus.topics = delete_duplicates(corpus.topics)

    corpus.check_unique()

    write_topics_with_subtopics(f"{db}-8.xlsx", corpus.topics)
    print(8, len(corpus.topics))
    # corpus.topics, neg3 = last_check_topics(corpus.topics)
    corpus.topics = delete_duplicates(corpus.topics)
    write_topics_with_subtopics(f"{db}-9.xlsx", corpus.topics)
    # write_topics("9-не прошли.xlsx", neg3)
    print(9, len(corpus.topics))

    corpus.topics = delete_subtopics(corpus.topics)
    write_topics_with_subtopics(f"{db}-10.xlsx", corpus.topics)
    print(10, len(corpus.topics))
    print(datetime.now() - time)

    nodes = list()
    edges = list()
    number = 0

    for t in corpus.topics:
        node_object = {"name": t.name}
        nodes.append(node_object)
        topic_number = number
        number += 1
        print(number)
        for n in t.news:
            node_object = {"title": n.translated['title'],
                           "url": n.url,
                           "country": n.country}
            nodes.append(node_object)
            print(number)
            edges.append((topic_number, number))
            number += 1

    draw_graph(nodes,edges, db)

