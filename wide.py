from corpus import Corpus, Topic
from utils import intersect, intersect_with_two
from xl_stats import write_topics, write_topics_with_subtopics
from datetime import datetime
from utils import iscountry, count_countries, count_not_countries
from utils import intersection_with_substrings, sublist, unite_news_text_and_topic_name
from utils import get_other, ContinueI, exists, more_than_one, delete_redundant, replace_presidents
from utils import get_topic_subtopic_nodes, get_topic_news_nodes

from draw_graph import draw_graph_with_topics
from text_processing.preprocess import STOP_WORDS, unite_countries_in, unite_countries_in_topic_names


COEFFICIENTS_1 = {"KA0": 0.35,
                  "KB0": 0.25,
                  "KC0": 0.16,
                  "KD0": 0.08,
                  "Kid": 1.5,
                  "KAY": 1.25,
                  "KBY": 0.38,
                  "KCY": 0.33,
                  "KDY": 0.27}

COEFFICIENTS_2 = {"a": 0.34,
                  "b": 0.34,
                  "c": 0.34,
                  "d": 0.1}

THRESHOLD = 0.75


with open("text_processing/between-words.txt", "r") as f:
    BETWEEN_WORDS = f.read().split('\n')


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
    new_topics = []
    for topic in topics:

        if count_not_countries(topic.name) >= 2 and count_countries(topic.name) >= 1:
            new_topics.append(topic)
    return new_topics


# 5
def filter_topics(topics, debug=False):

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
                + ids_coef

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


# 6
def add_news(topics, data):
    for topic in topics:
        for new in data:
            d = False
            new.all_text = new.description
            new.all_text.update(new.tokens['content'])

            if new not in topic.news:
                to_check = {0: list(topic.name),
                            1: new.uppercase_sequences}
                fio_in_name = unite_fio_in_two_strings(to_check, False)
                new_name = fio_in_name[0].intersection(fio_in_name[1])

                inters_1 = topic.name.intersection(new.all_text)
                new_name.update(inters_1)
                new_name = delete_redundant(new_name)

                to_check = {0: list(topic.new_name),
                            1: new.uppercase_sequences}
                fio_in_unique = unite_fio_in_two_strings(to_check, False)
                new_unique = fio_in_unique[0].intersection(fio_in_unique[1])

                inters_2 = topic.new_name.intersection(new.all_text)
                new_unique.update(inters_2)
                new_unique = delete_redundant(new_unique)

                if count_countries(new_name) >= 1 and count_not_countries(new_name) >= 2:
                            news_list = topic.news.copy()
                            news_list.append(new)

                            new_topic = Topic(new_name, news_list)
                            new_topic.new_name = new_unique

                            t, n = filter_topics([new_topic], d)
                            try:
                                top = t.pop()
                                topic.methods_for_news[new.id] = ["F", str(top.coefficient_sums["final_result"]),
                                                                  ', '.join(new_name), ', '.join(new_unique)]
                                topic.news.append(new)

                            except KeyError:
                                if new_unique and any(True for u in new_unique if u[0].isupper()):
                                    top = n.pop()
                                    if top.coefficient_sums["summ_1"] >= THRESHOLD:
                                        topic.methods_for_news[new.id] = ["E", str(top.coefficient_sums["summ_1"]),
                                                                         ', '.join(new_name), ', '.join(new_unique)]
                                        topic.news.append(new)

        topic.news = delete_dupl_from_news(topic.news)
    return topics


# 7
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

                if len(new_name) == 3 and len(upper_unique) >= 2 or len(new_name) > 3:
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
            s = add_news([s], corpus.data)[0]

    for t in topics:
        t.news = delete_dupl_from_news(t.news)
        for s in t.subtopics:
            s.news = delete_dupl_from_news(s.news)

    to_remove = set()

    for t in topics:
        if not t.subtopics:

            for ot in topics:

                if ot.subtopics:

                    if set(t.news).issubset(set(ot.news)):
                            extend_topic(ot, t)
                            to_remove.add(t)

                    elif len(t.news) > 2 and len(ot.news) > 2:
                            news_difference1 = {n for n in t.news if n not in ot.news}
                            news_difference2 = {n for n in ot.news if n not in t.news}
                            if len(news_difference1) <= 1 or len(news_difference2) <= 1:
                                extend_topic(ot, t)
                                to_remove.add(t)

    topics = [t for t in topics if t not in to_remove]

    for t in topics:
        t.news = delete_dupl_from_news(t.news)
        for s in t.subtopics:
            s.news = delete_dupl_from_news(s.news)

    return topics


def extend_topic(topic, other_topic):
    print(f"Extending topic {topic.name} with other {other_topic.name}")
    print(f"because news_ids: 1: {[n.id for n in topic.news]} 2: {[n.id for n in other_topic.news]}")
    topic.name = topic.name.union(other_topic.name)
    topic.new_name = topic.new_name.union(other_topic.new_name)

    topic.news.extend(other_topic.news)
    topic.subtopics.append(other_topic)
    return topic


# 8
def unite_subtopics(topics):
    for topic in topics:

        subtopic_indicators = {subtopic: False for subtopic in topic.subtopics}  # True if topic already added to other

        for subtopic in topic.subtopics:
            if not subtopic_indicators[subtopic]:
                other_subtopics = [s for s in topic.subtopics if s != subtopic and not subtopic_indicators[s]]
                for os in other_subtopics:
                    news_difference1 = {n for n in subtopic.news if n not in os.news}
                    news_difference2 = {n for n in os.news if n not in subtopic.news}
                    if len(news_difference1) <= 1 or len(news_difference2) <= 1:
                        subtopic.name.update(os.name)
                        subtopic.new_name.update(os.new_name)
                        subtopic.news.extend(os.news)
                        subtopic_indicators[os] = True
                        # subtopic_indicators[subtopic] = True

        topic.subtopics = delete_duplicates(topic.subtopics)
        topic.subtopics = {s for s in topic.subtopics if not subtopic_indicators[s]}
        if len(topic.subtopics) == 1:
            topic.subtopics = []

    return topics


# 11
def add_news_2(topics, data):

    def add_news_to_topic(topic, data):
        debug = False
        # if "Vladimir Putin" in topic.name:
        #     debug = True
        for new in data:
            if new not in topic.news:
                new.all_text.update(new.tokens['content'])
                name = unite_news_text_and_topic_name(new.all_text, topic.name)
                unique = unite_news_text_and_topic_name(new.all_text, topic.new_name)
                news = topic.news.copy()
                news.append(new)
                t = Topic(name, news)
                t.new_name = unique
                f, _ = filter_topics([t])
                if debug:
                    print("Common words", name)
                    print("Common unique", unique)
                    print("News ID", new.id)
                    print("Topic name", topic.name)
                if f:
                    topic.news.append(new)
                    new_t = f.pop()
                    topic.methods_for_news[new.id] = [str(new_t.coefficient_sums["final_result"]),
                                                      ', '.join(name), ', '.join(new_t.new_name)]
                    topic.news.append(new)
        topic.news = delete_dupl_from_news(topic.news)
        return topic

    new_topics = set()
    for i, topic in enumerate(topics):
        new_topic = add_news_to_topic(topic, data)

        for j, s in enumerate(topic.subtopics):
            sub = add_news_to_topic(s, data)
            new_topic.subtopics.append(sub)

        new_topics.add(new_topic)

    return new_topics


# 12
def add_minor_to_subtopics(topics):
    to_remove = set()
    for topic in topics:
        others = [t for t in topics if t != topic]
        topic_ids = {n.id for n in topic.news}

        for ot in others:
            ot_ids = {n.id for n in ot.news}
            if ot_ids.issubset(topic_ids) and ot_ids != topic_ids:
                to_remove.add(ot)
                topic.subtopics.append(ot)

    topics = [t for t in topics if t not in to_remove]
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


def delete_without_unique(topics):
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


if __name__ == '__main__':

    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    time = datetime.now()

    print("started working")

    """ Find initial topics """
    corpus = Corpus(db, table)
    corpus.find_topics()
    for topic in corpus.topics:
        topic.name = {w for w in topic.name if len(w) > 3 or w.isupper()}
    corpus.delete_small()
    write_topics(f"documents/{db}-0.xlsx", corpus.topics)
    print(0, len(corpus.topics))
    print(datetime.now() - time)

    """ Unite words in name + surname combinations """
    corpus.topics = unite_fio(corpus.topics)
    write_topics(f"documents/{db}-1.xlsx", corpus.topics)
    print(1, len(corpus.topics))
    print(datetime.now() - time)

    """ Leave only those that have more than 1 country and 2 not-country words in name """
    corpus.topics = check_topics(corpus.topics)
    write_topics(f"documents/{db}-2.xlsx", corpus.topics)
    print(2, len(corpus.topics))
    print(datetime.now() - time)

    """ Check uniqueness of each topic against others """
    """ And delete those without unique words or that have one small unique word"""
    for t in corpus.topics:
        t.name = replace_presidents(t.name)
    corpus.check_unique()
    corpus.topics = delete_without_unique(corpus.topics)
    write_topics(f"documents/{db}-3.xlsx", corpus.topics)
    print(3, len(corpus.topics))
    print(datetime.now() - time)

    """ Find sums according to specified coefficients for each topic and filter them using threshold """
    corpus.topics, neg = filter_topics(corpus.topics, False)
    write_topics(f"documents/{db}-5-прошли.xlsx", corpus.topics)
    write_topics(f"documents/{db}-5-не прошли.xlsx", neg)
    print(5, len(corpus.topics))
    print(datetime.now() - time)

    """ Add news to topics """
    corpus.topics = delete_without_unique(corpus.topics)
    # corpus.topics = add_news(corpus.topics, corpus.data)
    corpus.topics = delete_duplicates(corpus.topics)
    write_topics(f"documents/{db}-6.xlsx", corpus. topics)
    print(6, len(corpus.topics))
    print(datetime.now() - time)

    """ Delete redundant words from topic names """
    for t in corpus.topics:
        t.name = delete_redundant(t.name)

    """ Unite topics by news """
    topics_copy = {}
    corpus.topics = sorted(corpus.topics, key=lambda x: -len(x.name))
    corpus.topics = define_main_topics(corpus.topics)
    corpus.topics = delete_duplicates(corpus.topics)
    write_topics_with_subtopics(f"documents/{db}-7.xlsx", corpus.topics)
    print(7, len(corpus.topics))
    print(datetime.now() - time)

    """ Unite topics """
    corpus.topics = sorted(corpus.topics, key=lambda x: -len(x.name))
    corpus.topics = unite_subtopics(corpus.topics)
    write_topics_with_subtopics(f"documents/{db}-8.xlsx", corpus.topics)
    print(8, len(corpus.topics))
    print(datetime.now() - time)

    """ Delete duplicates in topics """
    corpus.topics = delete_duplicates(corpus.topics)
    write_topics_with_subtopics(f"documents/{db}-9.xlsx", corpus.topics)
    print(9, len(corpus.topics))
    print(datetime.now() - time)

    """ If a topic is small, it is 'eaten' by the bigger one """
    corpus.topics = delete_subtopics(corpus.topics)
    write_topics_with_subtopics(f"documents/{db}-10.xlsx", corpus.topics)
    print(10, len(corpus.topics))
    print(datetime.now() - time)

    # corpus.topics = add_news_2(corpus.topics, corpus.data)
    # write_topics_with_subtopics(f"documents/{db}-11.xlsx", corpus.topics)
    # print(11, len(corpus.topics))
    # print(datetime.now() - time)

    corpus.topics = add_minor_to_subtopics(corpus.topics)
    write_topics_with_subtopics(f"documents/{db}-12.xlsx", corpus.topics)
    print(12, len(corpus.topics))
    print(datetime.now() - time)

    nodes, edges = get_topic_news_nodes(corpus.topics)
    draw_graph_with_topics(nodes, edges, db)

    sub_nodes, sub_edges = get_topic_subtopic_nodes(corpus.topics)
    draw_graph_with_topics(sub_nodes, sub_edges, db+"1")
