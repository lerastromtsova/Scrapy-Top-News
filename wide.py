from corpus import Corpus, Topic
from xl_stats import write_topics, write_topics_with_subtopics, write_news
from datetime import datetime
from utils import iscountry, count_countries, count_not_countries
from utils import unite_news_text_and_topic_name, intersect
from utils import get_other, ContinueI, exists, more_than_one, delete_redundant, replace_presidents
from utils import get_topic_subtopic_nodes, get_topic_news_nodes
from utils import create_dir

from text_processing.preprocess import STOP_WORDS, unite_countries_in, unite_countries_in_topic_names
from coefs import COEFFICIENT_2_FOR_NEWS, COEFFICIENT_1_FOR_NEWS, COEFFICIENTS_2, COEFFICIENTS_1, THRESHOLD, \
                    COEF_FOR_FREQUENT, COEF_FOR_FREQUENT_UPPER, COEF_FOR_NEWS, COEF_FOR_NEWS_FIO
from time import sleep
from copy import deepcopy

with open("text_processing/between-words.txt", "r") as f:
    BETWEEN_WORDS = f.read().split('\n')

def delete_unique(topics):
    for t in topics:
        t.new_name = set()

    return topics


def unite_fio_in_two_strings(strings_to_check, debug=False):
    fios = {}
    fios[0] = set()
    fios[1] = set()

    check_len_1 = {}
    check_len_2 = {}
    check_len_4_all_big = {}
    check_len_4_some_small = {}

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
    return fios


# 1
def unite_fio(topics):
    """ Unite words in name + surname combinations """
    STOP_WORDS.append("house")
    debug = False
    for topic in topics:

        countries_in_name, _ = topic.countries(topic.name)
        small_in_name, _ = topic.small(topic.name)
        ids_in_name, _ = topic.ids(topic.name)
        # big_in_name, _ = topic.big(topic.name)
        # big_to_leave = {w for w in big_in_name if w in topic.frequent}

        fios = {}
        strs_to_check = {}
        to_remove = {}

        # if topic.news[0].id == 165 and topic.news[1].id == 125 or topic.news[0].id == 125 and topic.news[1].id == 16:
        #     debug = True

        to_remove[0] = set()
        to_remove[1] = set()

        fios[0] = set()
        fios[1] = set()

        strs_to_check[0] = topic.news[0].uppercase_sequences
        strs_to_check[0] = unite_countries_in(strs_to_check[0])
        strs_to_check[0] = [w for w in strs_to_check[0] if not iscountry(w)]

        strs_to_check[1] = topic.news[1].uppercase_sequences
        strs_to_check[1] = unite_countries_in(strs_to_check[1])
        strs_to_check[1] = [w for w in strs_to_check[1] if not iscountry(w)]

        if debug:
            print("ID1", topic.news[0].id)
            print(1, strs_to_check[0])
            print("ID2", topic.news[1].id)
            print(2, strs_to_check[1])

        if debug:
            print(topic.name)
            print(countries_in_name)

        # big_in_name = [w for w in topic.name if w in strings_to_check[0] or w in strings_to_check[1]]

        for word in topic.name:
            words_containing1 = {w for w in strs_to_check[0] if word in w and w != word}
            words_containing2 = {w for w in strs_to_check[1] if word in w and w != word}
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

        strs_to_check[0] = [w for w in strs_to_check[0] if w not in to_remove[0]]
        strs_to_check[1] = [w for w in strs_to_check[1] if w not in to_remove[1]]

        add_fios = unite_fio_in_two_strings(strs_to_check, debug)
        fios[0].update(add_fios[0])
        fios[1].update(add_fios[1])

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

        topic.name = {w for w in topic.name if len(w) > 3 or w.isupper()}

        topic.name = name
        topic.name = unite_countries_in(topic.name)
        topic.name = unite_countries_in_topic_names(topic.name)
        topic.name = {w for w in topic.name if w.lower() not in STOP_WORDS}
        topic.new_name = topic.name.copy()
        topic.frequent = topic.most_frequent()

    return topics


# 2
def check_topics(topics):
    """ Leave only those that have more than 1 country and 2 not-country words in name """
    new_topics = []
    for topic in topics:

        if count_not_countries(topic.name) >= 2 and count_countries(topic.name) >= 1:
            new_topics.append(topic)
    return new_topics


# 4
def filter_topics(topics, debug=False):
    """ Find sums according to specified coefficients for each topic and filter them using threshold """

    positive = set()

    for topic in topics:


        all_words, num_all_words = topic.all_words(topic.name)
        all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_countries_and_small(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        countries, num_countries = topic.countries(all_words)
        ids, num_ids = topic.ids(all_words)
        presidents, num_presidents = topic.presidents(all_words)
        num_fio -= num_presidents

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_countries_and_small(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, _ = topic.ids(unique_words)

        fio_coef0 = (num_fio - num_unique_fio) * COEFFICIENTS_1["KA0"]
        big_coef0 = (num_big - num_unique_big) * COEFFICIENTS_1["KB0"]
        small_coef0 = (num_small - num_unique_small) * COEFFICIENTS_1["KC0"]
        countries_coef0 = (num_countries - num_unique_countries) * COEFFICIENTS_1["KD0"]
        fio_coefY = num_unique_fio * COEFFICIENTS_1["KAY"]
        big_coefY = num_unique_big * COEFFICIENTS_1["KBY"]
        small_coefY = num_unique_small * COEFFICIENTS_1["KCY"]
        countries_coefY = num_unique_countries * COEFFICIENTS_1["KDY"]
        ids_coef = num_ids * COEFFICIENTS_1["Kid"]
        pres_coef = num_presidents * COEFFICIENTS_1["KE0"]

        fio_coef2 = COEFFICIENTS_2["a"] * exists(fio)
        big_coef2 = COEFFICIENTS_2["b"] * exists(big)
        small_coef2 = COEFFICIENTS_2["c"] * exists(small)
        countries_coef2 = COEFFICIENTS_2["d"] * more_than_one(countries)

        summ_1 = fio_coef0 \
                + big_coef0 \
                + small_coef0 \
                + countries_coef0 \
                + fio_coefY \
                + big_coefY \
                + small_coefY \
                + countries_coefY \
                + ids_coef\
                + pres_coef

        topic.sum_1 = summ_1

        summ_2 = fio_coef2 \
                 + big_coef2 \
                 + small_coef2\
                 + countries_coef2

        topic.sum_2 = summ_2

        final_result = summ_1 * summ_2

        topic.prod = final_result

        topic.coefficient_sums = {"fio_coef0": fio_coef0,
                                  "big_coef0": big_coef0,
                                  "small_coef0": small_coef0,
                                  "countries_coef0": countries_coef0,
                                  "fio_coefY": fio_coefY,
                                  "big_coefY": big_coefY,
                                  "small_coefY": small_coefY,
                                  "countries_coefY": countries_coefY,
                                  "fio_coef2": fio_coef2,
                                  "big_coef2": big_coef2,
                                  "small_coef2": small_coef2,
                                  "countries_coef2": countries_coef2,
                                  "ids_coef": ids_coef,
                                  "summ_1": summ_1,
                                  "summ_2": summ_2,
                                  "final_result": round(final_result, 3)}

        if final_result > THRESHOLD:
            positive.add(topic)

        if debug:
            print(all_words)
            print(fio)
            print(big)
            print(small)
            print(countries)
            print(ids)
            print(unique_words)
            print(topic.coefficient_sums)

    negative = {t for t in topics if t not in positive}

    return positive, negative


def add_news(topics, data, mode=1, count_unique=False):
    for topic in topics:

        debug = False

        freq_words = set(topic.most_frequent(COEFFICIENT_1_FOR_NEWS, True))
        freq_lower = {w for w in freq_words if w[0].islower()}

        flat_freq = [k.split() for k in freq_words]

        # if "helicopter" in topic.name:
        #     debug = True

        for new in data:
            d = False
            new.all_text = new.description
            new.all_text.update(new.tokens['content'])

            if new not in topic.news:
                to_check = {0: list(topic.name),
                            1: new.uppercase_sequences}
                fio_in_name = unite_fio_in_two_strings(to_check, False)
                new_name = fio_in_name[0].intersection(fio_in_name[1])

                inters_1 = topic.name.intersection(new.description.union(new.tokens["content"]))
                new_name.update(inters_1)
                new_name = delete_redundant(new_name)

                to_check = {0: list(topic.new_name),
                            1: new.uppercase_sequences}
                fio_in_unique = unite_fio_in_two_strings(to_check, False)
                new_unique = fio_in_unique[0].intersection(fio_in_unique[1])

                inters_2 = topic.new_name.intersection(new.all_text)
                new_unique.update(inters_2)
                new_unique = delete_redundant(new_unique)

                fio_in_new_name = [w for w in new_name if len(w.split()) >= 2]

                if mode == 1:
                    if new not in topic.news and count_countries(new_name):

                        if len(new_name) >= COEF_FOR_NEWS and len(fio_in_new_name) >= COEF_FOR_NEWS_FIO or len(new_name) == len(topic.name):
                            if count_unique:
                                if new_unique and len(new_name) != 3 or len(new_name) == 3 and len(new_unique) >= 2:
                                    topic.methods_for_news[new.id] = ["* "+", ".join(new_name)]
                                    news_list = topic.news.copy()
                                    news_list.append(new)

                                    new_topic = Topic(new_name, news_list)
                                    new_topic.new_name = new_unique

                                    t, n = filter_topics([new_topic], d)

                                    try:
                                        top = t.pop()
                                        topic.methods_for_news[new.id].extend(
                                            ["F", str(top.coefficient_sums["final_result"]),
                                             ', '.join(new_name), ', '.join(new_unique)])
                                        topic.news.append(new)

                                    except KeyError:
                                        # if len([u for u in new_unique if u[0].isupper() and not u.isupper()]) >= 2:
                                        #     top = n.pop()
                                        #     if top.coefficient_sums["summ_1"] >= THRESHOLD:
                                        #         topic.methods_for_news[new.id] = ["E", str(top.coefficient_sums["summ_1"]),
                                        #                                           ', '.join(new_name), ', '.join(new_unique)]
                                        #         topic.news.append(new)
                                        pass
                            else:
                                topic.methods_for_news[new.id] = ["* "+", ".join(new_name)]
                                news_list = topic.news.copy()
                                news_list.append(new)

                                new_topic = Topic(new_name, news_list)
                                new_topic.new_name = new_unique

                                t, n = filter_topics([new_topic], d)

                                try:
                                    top = t.pop()
                                    topic.methods_for_news[new.id].extend(
                                        ["F", str(top.coefficient_sums["final_result"]),
                                         ', '.join(new_name), ', '.join(new_unique)])
                                    topic.news.append(new)

                                except KeyError:
                                    # if len([u for u in new_unique if u[0].isupper() and not u.isupper()]) >= 2:
                                    #     top = n.pop()
                                    #     if top.coefficient_sums["summ_1"] >= THRESHOLD:
                                    #         topic.methods_for_news[new.id] = ["E", str(top.coefficient_sums["summ_1"]),
                                    #                                           ', '.join(new_name), ', '.join(new_unique)]
                                    #         topic.news.append(new)
                                    pass



                elif mode == 2:

                    flat_text = {w for k in new.all_text for w in k.split()}
                    common_freq = {w for w in flat_text if any(k for k in flat_freq if w in k)}
                    freq_diff = freq_words - common_freq

                    to_remove = set()
                    for word in common_freq:
                        for other_word in common_freq:
                            if word + ' ' + other_word in freq_words:
                                to_remove.add(word)
                            for oother_word in common_freq:
                                if word + ' ' + other_word+ ' ' + oother_word in freq_words:
                                    to_remove.add(word)
                                    to_remove.add(other_word)
                    common_freq -= to_remove

                    if debug:
                        print("Frequent: ", freq_words)
                        print("ID: ", new.id)
                        print("Common freq: ", common_freq)

                    common_upper = [w for w in common_freq if w[0].isupper() and not w.isupper()]
                    common_lower = [w for w in common_freq if w[0].islower()]

                    # if count_countries(new_name) and len(freq_words) >= 2 \
                    #     and freq_lower != freq_words and (freq_words == common_freq or
                    #     len(freq_words) >= 3 and len(freq_diff) == 1 and list(freq_diff)[0].islower()):
                    # if "Putin" in topic.name or "Vladimir Putin" in topic.name:
                    #     print("Topic: ", topic.name)
                    #     print(flat_freq)
                    #     print(flat_text)
                    #     print(new.id)
                    #     print(common_freq)
                    #     print("\n")
                    if count_countries(new_name) and len(freq_words) == len(common_freq) and (len(common_upper) >= 1
                                                                                              and len(common_lower) >= 1 or len(common_freq) > 2):

                            # print("Topic: ", topic.name)
                            # print("Frequent 50%: ", freq_words)
                            # print("Common frequent: ", common_freq)
                            # print("News ID: ", new.id)
                            # print("\n")
                            if new not in topic.news:

                                topic.news.append(new)

        if mode == 2:
            for s in topic.subtopics:

                freq_words = set(s.most_frequent(COEFFICIENT_1_FOR_NEWS, True))
                flat_freq = [k.split() for k in freq_words]

                for new in data:
                    if new not in s.news:
                        to_check = {0: list(s.name),
                                    1: new.uppercase_sequences}
                        fio_in_name = unite_fio_in_two_strings(to_check, False)
                        new_name = fio_in_name[0].intersection(fio_in_name[1])

                        inters_1 = s.name.intersection(new.description.union(new.tokens["content"]))
                        new_name.update(inters_1)
                        new_name = delete_redundant(new_name)

                        to_check = {0: list(s.new_name),
                                    1: new.uppercase_sequences}
                        fio_in_unique = unite_fio_in_two_strings(to_check, False)
                        new_unique = fio_in_unique[0].intersection(fio_in_unique[1])

                        inters_2 = s.new_name.intersection(new.all_text)
                        new_unique.update(inters_2)
                        new_unique = delete_redundant(new_unique)

                        flat_text = {w for k in new.all_text for w in k.split()}
                        common_freq = {w for w in flat_text if any(k for k in flat_freq if w in k)}
                        to_remove = set()
                        for word in common_freq:
                            for other_word in common_freq:
                                if word + ' ' + other_word in freq_words:
                                    to_remove.add(word)
                                for oother_word in common_freq:
                                    if word + ' ' + other_word + ' ' + oother_word in freq_words:
                                        to_remove.add(word)
                                        to_remove.add(other_word)
                        common_freq -= to_remove
                        common_upper = [w for w in common_freq if w[0].isupper() and not w.isupper()]
                        common_lower = [w for w in common_freq if w[0].islower()]

                        if count_countries(new_name) and len(freq_words) == len(common_freq) and new_unique and new not in s.news \
                                and (len(common_upper) >= 1 and len(common_lower) >= 1 or len(common_freq) > 2):
                            s.news.append(new)

        topic.news = delete_dupl_from_news(topic.news)
    return topics


# 6
def define_main_topics(topics):
    marked_subtopics = {topic: False for topic in topics}

    debug = False

    for i, topic in enumerate(topics):
        topic_copy = Topic(topic.name.copy(), topic.news.copy())
        topic_copy.new_name = topic.new_name.copy()
        topic.subtopics.append(topic_copy)
        for j in range(i+1, len(topics)-1):
            other_topic = topics[j]

            if not marked_subtopics[other_topic]:
                new_name = unite_news_text_and_topic_name(topic.name, other_topic.name)
                new_unique = unite_news_text_and_topic_name(topic.new_name, other_topic.new_name)

                upper_unique = {u for u in new_unique if u[0].isupper()}

                if len(new_name) == 3 and len(upper_unique) >= 2 or len(new_name) != 3:
                    news_list = list(set(topic.news).union(set(other_topic.news)))
                    new_topic = Topic(new_name, news_list)
                    new_topic.new_name = new_unique
                    t, _ = filter_topics([new_topic])
                    if t:
                        extend_topic(topic, other_topic)
                        marked_subtopics[other_topic] = True
                    elif len(new_unique) >= 2:
                        extend_topic(topic, other_topic)
                        marked_subtopics[other_topic] = True

    to_remove = set()
    for t in topics:
        for ot in topics:
            if t in ot.subtopics:
                to_remove.add(t)

    topics = [t for t in topics if t not in to_remove]

    for t in topics:
        if len(t.subtopics) == 1:
            t.subtopics = []

    for t in topics:
        t = add_news([t], corpus.data)[0]
        for s in t.subtopics:
            s = add_news([s], corpus.data, count_unique=True)[0]

    for t in topics:
        t.news = delete_dupl_from_news(t.news)
        for s in t.subtopics:
            s.news = delete_dupl_from_news(s.news)

    return topics


# 7
def delete_without_frequent(topics):
    for t in topics:

        freq = t.most_frequent(COEFFICIENT_2_FOR_NEWS, with_fio=True)

        for i, n in enumerate(t.news):
            if i >= 2:
                text = n.all_text.union(n.tokens['content'])
                freq_text = unite_news_text_and_topic_name(text, freq)
                freq_upper = [w for w in freq_text if w[0].isupper() and not w.isupper()]
                if len(freq_text) <= COEF_FOR_FREQUENT or len(freq_upper) < COEF_FOR_FREQUENT_UPPER:
                    t.news[i] = None
                elif len(freq) < COEF_FOR_FREQUENT:
                    if len(freq_text) <= len(freq) or len(freq_upper) < COEF_FOR_FREQUENT_UPPER:
                        t.news[i] = None
                    else:
                        try:
                            t.methods_for_news[n.id].insert(0, 'Frequent common words: '+', '.join(freq_text))
                            t.methods_for_news[n.id].insert(0, 'Frequent common words (uppercase): '+', '.join(freq_upper))
                        except KeyError:
                            t.methods_for_news[n.id] = []
                            t.methods_for_news[n.id].insert(0, 'Frequent common words: ' + ', '.join(freq_text))
                            t.methods_for_news[n.id].insert(0, 'Frequent common words (uppercase): ' + ', '.join(freq_upper))

                else:
                    try:
                        t.methods_for_news[n.id].insert(0, 'Frequent common words: ' + ', '.join(freq_text))
                        t.methods_for_news[n.id].insert(0, 'Frequent common words (uppercase): ' + ', '.join(freq_upper))
                    except KeyError:
                        t.methods_for_news[n.id] = []
                        t.methods_for_news[n.id].insert(0, 'Frequent common words: ' + ', '.join(freq_text))
                        t.methods_for_news[n.id].insert(0, 'Frequent common words (uppercase): ' + ', '.join(freq_upper))
        t.news = [n for n in t.news if n]
        if t.subtopics:
            t.subtopics = delete_without_frequent(t.subtopics)
        for s in t.subtopics:
            for n in s.news:
                if n not in t.news:
                    t.news.append(n)
            t.news = delete_dupl_from_news(t.news)
            # t.news = list(set(t.news).union(set(s.news)))
    topics = [t for t in topics if t.news]
    return topics


# 8
def add_news_and_delete_duplicates(topics):

    topics = add_news(topics, corpus.data, 2)

    # to_remove = set()

    # for t in topics:
    #     if not t.subtopics:
    #
    #         for ot in topics:
    #
    #             if ot.subtopics:
    #
    #                 if set(t.news).issubset(set(ot.news)):
    #                         extend_topic(ot, t)
    #                         to_remove.add(t)
    #
    #                 elif len(t.news) > 2 and len(ot.news) > 2:
    #                         news_difference1 = {n for n in t.news if n not in ot.news}
    #                         news_difference2 = {n for n in ot.news if n not in t.news}
    #                         if len(news_difference1) <= 1 or len(news_difference2) <= 1:
    #                             extend_topic(ot, t)
    #                             to_remove.add(t)
    #
    # topics = [t for t in topics if t not in to_remove]

    for t in topics:
        t.news = delete_dupl_from_news(t.news)
        for s in t.subtopics:
            s.news = delete_dupl_from_news(s.news)

    return topics


def extend_topic(topic, other_topic, add_subtopics=False):
    # print(f"Extending topic {topic.name} with other {other_topic.name}")
    # print(f"because news_ids: 1: {[n.id for n in topic.news]} 2: {[n.id for n in other_topic.news]}")

    topic.name = topic.name.union(other_topic.name)

    topic.new_name = topic.new_name.union(other_topic.new_name)
    topic.news.extend(other_topic.news)
    try:
        topic.subtopics.append(other_topic)
    except AttributeError:
        topic.subtopics.add(other_topic)

    if add_subtopics:
        try:
            topic.subtopics.extend(other_topic.subtopics)
        except AttributeError:
            topic.subtopics.update(other_topic.subtopics)

    return topic


def delete_dupl_from_subtopics(subtopics):
    to_remove = set()
    for s in subtopics:
        if s not in to_remove:
            others = [os for os in subtopics if os != s]
            for o in others:
                if o not in to_remove:
                    ids1 = {n.id for n in s.news}
                    ids2 = {n.id for n in o.news}
                    if ids1 == ids2:
                        to_remove.add(o)
    return [s for s in subtopics if s not in to_remove]


# 12
def unite_subtopics(topics):
    for topic in topics:

        subtopic_indicators = {subtopic: False for subtopic in topic.subtopics}  # True if topic already added to other

        for subtopic in topic.subtopics:
            if not subtopic_indicators[subtopic]:
                other_subtopics = [s for s in topic.subtopics if s != subtopic and not subtopic_indicators[s]]
                for os in other_subtopics:
                    news_difference1 = {n for n in subtopic.news if n not in os.news}
                    news_difference2 = {n for n in os.news if n not in subtopic.news}

                    if len(news_difference1) <= 1 and len(news_difference2) <= 1:
                        print("Updating: ", subtopic.name, "with ", os.name)
                        subtopic.name.update(os.name)
                        subtopic.new_name.update(os.new_name)
                        subtopic.news.extend(os.news)
                        subtopic_indicators[os] = True
                        subtopic.news = delete_dupl_from_news(subtopic.news)
                        # subtopic_indicators[subtopic] = True

        topic.subtopics = delete_dupl_from_subtopics(topic.subtopics)
        topic.subtopics = {s for s in topic.subtopics if not subtopic_indicators[s]}
        if len(topic.subtopics) == 1:
            topic.subtopics = set()

    return topics


def delete_duplicates(topics):
    topics = list(topics)
    for i, t in enumerate(topics):
        if t:
            others = [to for to in topics if to is not None]
            others = [to for to in others if t.name != to.name]
            ids = {new.id for new in t.news}
            for o in others:
                if o:
                    other_ids = {n.id for n in o.news}
                    if ids == other_ids:
                        o.name |= t.name
                        topics[i] = None
                    if t.name.issubset(o.name):
                        topics[i] = None
    topics = {t for t in topics if t is not None}
    topics = list(topics)
    return topics


def delete_dupl_from_news(news_list):
    new = list()
    for n in news_list:
        ids = {i.id for i in new}
        if n.id not in ids:
            new.append(n)
    return new


def delete_without_unique(topics):
    """ Delete without unique """
    to_remove = set()

    for t in topics:
        unique_copy = t.new_name.copy()
        unique_in_name = unique_copy.intersection(t.name)
        if not unique_copy or (len(unique_copy) == 1 and unique_copy.pop()[0].islower()) or (len(t.name) == 3 and len(unique_in_name) < 2):
            to_remove.add(t)
        else:
            # Here we delete words if they are in some word combination in topic name
            t.name = delete_redundant(t.name)

    topics = [t for t in topics if t not in to_remove]

    return topics


# 9,12
def unite_by_news(topics):
    to_remove = []

    for t in topics:
        cop = Topic(t.name.copy(), t.news.copy())
        cop.new_name = t.new_name.copy()
        extend_topic(t, cop)

    for t in topics:
        if t.name not in to_remove:
            similar = list()
            for ot in topics:
                if ot.name not in to_remove:
                    if ot.name != t.name:
                        common_news = set(ot.news).intersection(set(t.news))
                        countries_in_common = {n.country for n in common_news}
                        if len(countries_in_common) >= 2:
                            similar.append(ot)

            most_similar = filter(lambda a: len(a.news) == max([len(t.news) for t in similar]), similar)

            for ms in most_similar:
                extend_topic(t, ms, True)
                print(
                    f"Extending topic {t} with {ms} because common news {', '.join([str(n.id) for n in set(ms.news).intersection(set(t.news))])}")
                to_remove.append(ms.name)

    topics = [t for t in topics if t not in to_remove]

    for t in topics:
        t.news = delete_dupl_from_news(t.news)
        for s in t.subtopics:
            s.news = delete_dupl_from_news(s.news)

    for t in topics:
        if len(t.subtopics) == 1 and list(t.subtopics)[0].name == t.name:

            t.subtopics = set()

    topics = delete_duplicates(topics)

    # for t in topics:
    #     for s in t.subtopics:
    #         t.new_name |= s.new_name

    return topics


# 11
def form_new_wide(topics, data):
    small_topics = [t for t in topics if len(t.news)==2]
    news_in_small = [n for t in small_topics for n in t.news]
    counts = {n.id: news_in_small.count(n) for n in set(news_in_small)}
    to_remove = set()
    for id, count in counts.items():
        if count == max(counts.values()) and count > 1:
            news_item = [n for n in data if n.id==id][0]
            new_topic = Topic(name={news_item.translated["title"]}, init_news=[news_item])
            for st in small_topics:
                ids = {new.id for new in st.news}
                if id in ids:
                    new_topic.subtopics.append(st)
                    new_topic.news.append(news_item)
                    to_remove.add(st)
            if new_topic.subtopics:
                topics.append(new_topic)
    topics = [t for t in topics if t not in to_remove]
    return topics


def simple_report(topics, num_points, start_time, db_name):
    if news_ids == "All":
        write_topics(f"documents/{db_name}-{num_points}-{news_ids}.xlsx", topics)
    else:
        write_topics(f"documents/{db_name}-{num_points}-{','.join(news_ids)}.xlsx", topics)
    print(num_points, len(topics))
    print(datetime.now() - start_time)
    if with_graphs:
            nodes, edges = get_topic_news_nodes(topics)
            # draw_graph_with_topics(nodes, edges, db_name + f" {num_points}")


def subtopics_report(topics, num_points, start_time, db_name, freq_fio=False, freq_new_fio=False):
    if news_ids == "All":
        write_topics_with_subtopics(f"documents/{db_name}-{num_points}-{news_ids}.xlsx", topics, freq_fio, freq_new_fio)
    else:
        write_topics_with_subtopics(f"documents/{db_name}-{num_points}-{','.join(news_ids)}.xlsx", topics, freq_fio, freq_new_fio)
    print(num_points, len(topics))
    print(datetime.now() - start_time)
    if with_graphs:
            nodes, edges = get_topic_subtopic_nodes(topics)
            # draw_graph_with_topics(nodes, edges, db_name + f" {num_points}")


def add_news_by_frequent(topics, data):
    for t in topics:
        debug = False
        freq = t.most_frequent(COEFFICIENT_1_FOR_NEWS, True)
        fio_in_freq = [w for w in freq if len(w.split()) >= 2]
        if len(freq) >= 4 or len(freq) == 3 and len(fio_in_freq) >= 1:
            if debug:
                print("Frequent 50%", freq)
                print(fio_in_freq)
            for n in data:
                if n not in t.news:
                    common_freq = unite_news_text_and_topic_name(freq, n.all_text)
                    common_freq1 = unite_news_text_and_topic_name(n.all_text, freq)
                    common_freq |= common_freq1
                    if debug:
                        print("Common", common_freq)
                    if len(common_freq) == len(freq):
                        if debug:
                            print("Adding news: ", n.id)
                        t.news.append(n)
    return topics


# 12
def add_news_to_subtopics(topics):
    for t in topics:
        for s in t.subtopics:
            for n in t.news:
                if n not in s.news:
                    common_unique = n.all_text.intersection(s.new_name)
                    cu_lower = [w for w in common_unique if w[0].islower()]
                    cu_upper = [w for w in common_unique if w[0].isupper() and not w.isupper()]
                    if len(cu_lower) >= 2 or len(cu_upper) >= 1:
                        s.news.append(n)
    return topics


def create_copy_of_topics(topics):
    copy_topics = list()
    for t in topics:
        new = Topic(t.name.copy(), t.news.copy())
        new.new_name = t.new_name.copy()
        for s in t.subtopics:
            snew = Topic(s.name.copy(), s.news.copy())
            snew.new_name = s.new_name.copy()
            new.subtopics.append(snew)
        copy_topics.append(t)
    return copy_topics


if __name__ == '__main__':

    db = input("DB name (default - day): ")
    table = input("Table name (default - News): ")
    with_graphs = input("Draw graphs? default - no, print any letter to draw graphs: ")
    news_ids = input("Input News IDs").split()
    only_english = input("Only translate to English? Default - no, print any letter to use only English: ")
    countries = input("Countries: ").split(', ')

    if not db:
        db = "day"
    if not table:
        table = "News"
    if not news_ids:
        news_ids = "All"
    if not only_english:
        only_english = False

    if countries[0] == '':
        countries = "All"

    time = datetime.now()

    print(f"Started working at {time}")

    create_dir('documents')

    corpus = Corpus(db, table, news_ids, countries)

    if only_english:
        write_news(f"documents/{db}-{only_english}-{news_ids}.xlsx", corpus.data)

    else:

        if with_graphs:
            # 1) график по 2 общим словам без стран
            corpus.find_topics(mode={"country": 0, "not_country": 2})
            nodes, edges = get_topic_news_nodes(corpus.topics)
            # draw_graph_with_topics(nodes, edges, db+" 2общ. без стран")
            corpus.topics = []

        corpus.find_topics()  # объединяем новости по 1 стране и 2 нестранам по всему тексту
        for topic in corpus.topics:
            topic.name = {w for w in topic.name if len(w) > 3 or (w.isupper() and len(w) > 2)}  # выкидываем из общих слов
            # те, у которых длина меньше или равна 3 (строчное ) или 2 (заглавное)

        corpus.delete_small()  # удаляем темы, у которых важные слова входят в важные слова другой темы
        # удаляем темы, которые идентичны друг другу

        simple_report(corpus.topics, 0, time, db)

        corpus.topics = delete_duplicates(corpus.topics)  # удаляем дублирующие темы (еще раз!)
        corpus.topics = unite_fio(corpus.topics)  # объединяем ФИО

        simple_report(corpus.topics, 1, time, db)

        corpus.topics = delete_duplicates(corpus.topics)   # удаляем дублирующие темы (еще раз!)
        corpus.topics = check_topics(corpus.topics)  # оставляем только те темы, у которых 1с 2нс

        simple_report(corpus.topics, 2, time, db)

        for t in corpus.topics:
            t.name = replace_presidents(t.name, mode="add")  # replace presidents with countries - нужен динамичный список президентов!
            t.new_name = replace_presidents(t.new_name, mode="remove")

        corpus.sort_topics()  # сортируем по длине имени
        corpus.check_unique()  # какие-то правила объединения тем ??????

        for t in corpus.topics:
            t.name = delete_redundant(t.name)  # удаляем слова, входящие в другие слова
            t.name = {w for w in t.name if not any((w1 for w1 in t.name - {w} if w1.lower() in w.lower()))}  # делаем то же самое??? лол
            t.new_name = delete_redundant(t.new_name)
            t.new_name = {w for w in t.new_name if not any((w1 for w1 in t.new_name - {w} if w1.lower() in w.lower()))}

        corpus.topics = delete_without_unique(corpus.topics)  # удаляем темы, которые не имеют уникальных слов
        # (и какое-то отдельное правило для тем из 3 слов)

        simple_report(corpus.topics, 3, time, db)

        corpus.topics, neg = filter_topics(corpus.topics, False)  # применяем коэффициенты, чтобы отсеять темы

        simple_report(corpus.topics, 4, time, db)

        corpus.topics = delete_without_unique(corpus.topics)
        corpus.topics = delete_duplicates(corpus.topics)

        simple_report(corpus.topics, 5, time, db)

        for t in corpus.topics:
            t.name = delete_redundant(t.name)

        topics_copy = {}
        corpus.sort_topics()
        corpus.topics = define_main_topics(corpus.topics)  # распределяем темы по подтемам по каким-то коэффициентам
        corpus.topics = delete_duplicates(corpus.topics)

        subtopics_report(corpus.topics, 6, time, db, False)

        corpus.topics = delete_without_frequent(corpus.topics)  # удаляем новости без частотных слов
        subtopics_report(corpus.topics, 7, time, db, freq_fio=False, freq_new_fio=True)

        corpus.topics = add_news_and_delete_duplicates(corpus.topics)  # добавляем новости функцией add_news и удаляем дубликаты из новостей
        subtopics_report(corpus.topics, 8, time, db, freq_fio=True, freq_new_fio=True,)

        corpus.sort_topics()
        corpus.topics = unite_by_news(corpus.topics)  # объединяем темы по 2 новостям из разных стран

        subtopics_report(corpus.topics, 9, time, db, freq_fio=True, freq_new_fio=True,)

        corpus.topics = add_news_by_frequent(corpus.topics, corpus.data)  # Добавляем новости по 4 частотным словам или 3 частотным, если хотя бы одно из них ФИО

        subtopics_report(corpus.topics, 10, time, db, freq_fio=True, freq_new_fio=True)

        corpus.topics = unite_by_news(corpus.topics)  # объединяем темы по 2 новостям из разных стран

        subtopics_report(corpus.topics, 11, time, db, freq_fio=True, freq_new_fio=True)

        corpus.topics = add_news_to_subtopics(corpus.topics)  # добавляем новости к подтемам по 2 общим заглавным уникальным и 2 общим строчным уникальным

        subtopics_report(corpus.topics, 12, time, db, freq_fio=True, freq_new_fio=True)

        for k in range(3):
            corpus.topics = unite_subtopics(corpus.topics)  # объединяем подтемы если у них различие меньше чем в 1 новость

        subtopics_report(corpus.topics, 13, time, db, freq_fio=True, freq_new_fio=True)

        # for t in corpus.topics:
        #     print("Main: ", ", ".join({str(n.id) for n in t.news}))
        #     for s in t.subtopics:
        #         print("Micro: ", ", ".join({str(n.id) for n in s.news}))

        corpus.topics = form_new_wide(corpus.topics, corpus.data)  # каким-то образом формируем новые темы и подтемы для них

        subtopics_report(corpus.topics, 14, time, db, freq_fio=True, freq_new_fio=True)

        corpus.topics = unite_by_news(corpus.topics) # объединяем темы по 2 новостям из разных стран

        subtopics_report(corpus.topics, 15, time, db, freq_fio=True, freq_new_fio=True,)
