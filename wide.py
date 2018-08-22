from descr import CorpusD, count_countries, count_not_countries
from content import CorpusC
from content import Topic
from xl_stats import write_topics
from datetime import datetime
from descr import intersect, iscountry
from math import ceil
from text_processing.preprocess import PUNKTS
from string import punctuation
from text_processing.preprocess import split_into_sentences, split_into_paragraphs, preprocess
import cProfile

# def profile(func):
#     """Decorator for run function profile"""
#     def wrapper(*args, **kwargs):
#         profile_filename = func.__name__ + '.txt'
#         profiler = cProfile.Profile()
#         result = profiler.runcall(func, *args, **kwargs)
#         profiler.dump_stats(profile_filename)
#         return result
#     return wrapper
#
# @profile
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
            freq_words = freq_words[:ceil(len(freq_words)/2)]

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
                        if len(cw_in_unique)/len(t.new_name) > 0.5 and len(cw_in_unique)/len(o.new_name) > 0.5:
                            print("F", o.name, t.name)
                            similar.add(o)
                            continue

                        # g
                        if (len(common_freq)/len(freq_words) > 0.5 and len(common_freq)/len(freq_words1) > 0.5) and len(cw_in_unique) >= 1:
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

    for i,t in enumerate(topics):
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

                                not_unique_cw = {word for word in cw-unique_cw if word[0].islower()}

                                if unique_cw and not_unique_cw:

                                    topic.obj.update(cw)
                                    new_topics.add(topic)

        cw_in_descr = topic.news[0].description.intersection(topic.news[1].description)

        topic.objects = {o for o in topic.objects if len(o)>2}
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
            topic.name.update(topic.news[0].named_entities['content'].intersection(topic.news[1].named_entities['content']))

    return topics


TITLES = {"President", "Chancellor", "Democrat", "Governor", "King", "Queen"}


def unite_entities(topics):
    for topic in topics:

        for i in range(2):

            ent_dict = {}

            if i == 0:
                j = 1
            else:
                j = 0

            for ent1 in topic.news[i].named_entities['content']:
                for ent2 in topic.news[i].named_entities['content']:
                    if ent1 not in TITLES and ent2 not in TITLES:
                        st = ent1 + ' ' + ent2

                        text = topic.news[j].translated['content'].split()
                        # i1 = text.index(ent1)
                        # i2 = text.index(ent2)

                        if ent1 in text:

                            previous_word1 = text[text.index(ent1)-1]
                            next_word1 = text[text.index(ent1)+1]

                        if ent2 in text:
                            previous_word2 = text[text.index(ent2) - 1]
                            next_word2 = text[text.index(ent2) + 1]

                        if topic.news[i].translated['content'].count(st) >= 2 or topic.news[j].translated['content'].count(st) >= 2:
                            ent_dict[ent1] = st
                            ent_dict[ent2] = st
                            continue

                        elif st in topic.news[i].translated['content'] and st in topic.news[j].translated['content']:
                            ent_dict[ent1] = st
                            ent_dict[ent2] = st
                            continue
                        # elif st in topic.news[0].translated['content'] and ent1 in text:
                        elif st in topic.news[i].translated['content'] and ent1 in text and previous_word1.islower() \
                                and previous_word1 not in punctuation and previous_word1 not in PUNKTS \
                                and next_word1.islower() and next_word1 not in punctuation and next_word1 not in PUNKTS:
                            try:
                                # if text[text.index(ent1)-1][0].islower() and text[text.index(ent1)+1][0].islower():
                                    ent_dict[ent1] = st
                                    ent_dict[ent2] = st

                            except IndexError:
                                pass
                        # elif st in topic.news[0].translated['content'] and ent2 in text:
                        elif st in topic.news[i].translated['content'] and ent2 in text \
                                and previous_word2.islower() \
                                and previous_word2 not in punctuation and previous_word2 not in PUNKTS \
                                and next_word2.islower() and next_word2 not in punctuation and next_word2 not in PUNKTS:
                            try:
                                # if text[text.index(ent2)-1][0].islower() and text[text.index(ent2)+1][0].islower():
                                    ent_dict[ent1] = st
                                    ent_dict[ent2] = st
                            except IndexError:
                                pass

            nes_content = topic.news[i].named_entities['content'].copy()

            for ent in topic.news[i].named_entities['content']:
                if ent in ent_dict.keys():
                    nes_content.remove(ent)
                    nes_content.add(ent_dict[ent])

            topic.news[i].named_entities['content'] = nes_content

            nes_descr = topic.news[i].description.copy()

            for ent in topic.news[i].description:
                if ent in ent_dict.keys():
                    nes_descr.remove(ent)
                    nes_descr.add(ent_dict[ent])

            topic.news[i].description = nes_descr

        if any(w for w in topic.name if w[0].islower()):
            topic.name = intersect(topic.news[0].description, topic.news[1].description)
        else:
            topic.name = intersect(topic.news[0].named_entities['content'], topic.news[1].named_entities['content'])

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
                result_set.add(item1)
            elif item2 in item1.split():
                result_set.add(item2)
    return result_set


if __name__ == '__main__':
    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
            db = "day"
    if not table:
            table = "buffer"

    time = datetime.now()

    c_descr = CorpusD(db, table)
    c_descr.find_topics()
    write_topics("Descriptions.xlsx", c_descr.topics)

    c_descr.delete_small()
    c_descr.check_unique()
    c_descr.topics = unite_entities(c_descr.topics)
    c_descr.topics = [t for t in c_descr.topics if t.isvalid()]

    c_content = CorpusC(db, table)
    c_content.find_topics()
    write_topics("Texts.xlsx", c_content.topics)

    c_content.delete_small()
    # write_topics("1-texts.xlsx", c_content.topics)

    c_content.check_unique()
    # write_topics("2-texts.xlsx", c_content.topics)

    c_content.topics = unite_entities(c_content.topics)
    # write_topics("3-texts.xlsx", c_content.topics)

    c_content.topics = [t for t in c_content.topics if t.isvalid()]
    # write_topics("4-texts.xlsx", c_content.topics)

    all_topics = c_descr.topics
    all_topics.extend(c_content.topics)

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

    print(datetime.now()-time)
