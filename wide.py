from descr import CorpusD, count_countries, count_not_countries
from content import CorpusC
from content import Topic
from xl_stats import write_topics


def similar(topics):

    new_topics = list()

    for t in topics:
        if t is not None:
            others = []
            for to in topics:
                if to and set(to.news) != set(t.news):
                    others.append(to)

            similar = {t}
            for o in others:
                if o is not None:
                    try:

                        # cw1 = t.name.intersection(o.name)
                        # cw2 = t.text_name.intersection(o.text_name)
                        # cw3 = t.main_words.intersection(o.main_words)
                        # if cw1:
                        #     percent1 = len(cw1) / len(t.name)
                        #     percent2 = len(cw1) / len(o.name)
                        # else:
                        #     percent1 = 0.0
                        #     percent2 = 0.0
                        #
                        # if cw2:
                        #     percent3 = len(cw2) / len(t.text_name)
                        #     percent4 = len(cw2) / len(o.text_name)
                        # else:
                        #     percent3 = 0.0
                        #     percent4 = 0.0
                        #
                        # if cw3:
                        #     percent5 = len(cw3) / len(t.text_name)
                        #     percent6 = len(cw3) / len(o.text_name)
                        # else:
                        #     percent5 = 0.0
                        #     percent6 = 0.0

                        # common_news = set(t.news).intersection(set(o.news))
                        # countries = {c.country for c in common_news}
                        #
                        # if common_news:
                        #     percent7 = len(common_news) / len(t.news)
                        #     percent8 = len(common_news) / len(o.news)
                        # else:
                        #     percent7 = 0.0
                        #     percent8 = 0.0
                        #
                        # if percent7 > 0.5 and percent8 > 0.5:
                        #     similar.add(o)
                        common_unique = t.unique_words.intersection(o.unique_words)
                        if common_unique:
                            print(common_unique)
                        common_main = t.main_words.intersection(o.main_words)
                        if common_main:
                            print(common_main)
                        if count_countries(common_main) >= 1 and count_not_countries(common_main) >= 2:
                            print(t.name, o.name)
                            similar.add(o)

                    except ZeroDivisionError:
                        continue
            new_topic = Topic(t.name, init_news=t.news)
            for s in similar:
                new_topic.name.update(s.name)
                for n in s.news:
                    if n not in new_topic.news:
                        new_topic.news.extend(s.news)
                new_topic.subtopics.add(s)
                topics[topics.index(s)] = None
            new_topic.news = list(set(new_topic.news))

            new_topics.append(new_topic)

    return new_topics

def give_news(topics, rows):
    for row in rows:
        for topic in topics:
            percent1 = len(topic.name.intersection(row.named_entities['content']))/len(topic.name)
            percent2 = len(topic.name.intersection(row.description))/len(topic.name)
            percent3 = len(topic.main_words.intersection(row.named_entities['content']))/len(topic.name)
            percent4 = len(topic.main_words.intersection(row.description)) / len(topic.name)

            keywords = {w for w in topic.unique_words if w in row.description}
            if (percent1 > 0.5 and percent3 > 0.5 or percent2 > 0.5 and percent4 > 0.5) and len(keywords) >= 1:
                if row not in topic.news:
                    topic.news.append(row)
    return topics

def assign_news(topics, rows):

    for row in rows:
        key_words = row.description
        key_words.update(row.named_entities['content'])
        for topic in topics:
            if topic.name.issubset(key_words):
                if row not in topic.news:
                    topic.news.append(row)
            topic.subtopics = []

    for topic in topics:
        topic.news = list(set(topic.news))
    return topics


def delete_duplicates(topics):
    new_topics = topics.copy()
    to_remove = set()
    to_add = set()

    for t in topics:
        others = [to for to in topics if t.name != to.name]
        for o in others:
            if set(o.news) == set(t.news):
                if o in new_topics and t in new_topics:
                    new_topics.remove(t)

    return new_topics


db = input("DB name (default - day): ")
table = input("Table name (default - buffer): ")

if not db:
        db = "day"
if not table:
        table = "buffer"


c_descr = CorpusD(db, table)
c_descr.find_topics()
# write_topics("0-краткое.xlsx", c_descr.topics)
c_descr.delete_small()
# write_topics("1-краткое.xlsx", c_descr.topics)
c_descr.check_unique()
# write_topics("2-краткое.xlsx", c_descr.topics)
c_descr.topics = [t for t in c_descr.topics if t.isvalid()]
# write_topics("3-краткое.xlsx", c_descr.topics)
c_descr.final_delete()
# write_topics("4-краткое.xlsx", c_descr.topics)

c_content = CorpusC(db, table)

c_content.find_topics()
# write_topics("0-тексты.xlsx", c_content.topics)
c_content.delete_small()
# write_topics("1-тексты.xlsx", c_content.topics)
c_content.check_unique()
# write_topics("2-тексты.xlsx", c_content.topics)
c_content.topics = [t for t in c_content.topics if t.isvalid()]
# write_topics("3-тексты.xlsx", c_content.topics)

all_topics = c_descr.topics
all_topics.extend(c_content.topics)
all_topics = give_news(all_topics, c_descr.data)

write_topics("0.xlsx", all_topics)

all_topics = similar(all_topics)
all_topics = delete_duplicates(all_topics)

write_topics("3.xlsx", all_topics)

all_topics = assign_news(all_topics, c_descr.data)
all_topics = delete_duplicates(all_topics)

write_topics("6.xlsx", all_topics)
