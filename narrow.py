from descr import CorpusD
from content import CorpusC
from content import Topic
from xl_stats import write_topics


def unique(topics):

    to_remove = set()

    for topic in topics:
        topic.new_name = topic.name.copy()

    for topic in topics:
        others = [t for t in topics if topic.name != t.name and set(topic.news) != set(t.news)]
        flag = True
        for other in others:
            cw = topic.name.intersection(other.name)
            percent1 = len(cw)/len(topic.name)
            percent2 = len(cw)/len(other.name)
            if percent1 >= 0.5 and percent2 >= 0.5:
                flag = False
                topic.new_name -= cw
        if flag:
            to_remove.add(topic)

    for topic in topics:
        if len(topic.new_name)<2:
            to_remove.add(topic)

    topics = [t for t in topics if t not in to_remove]
    return topics

def assign_news(topics, rows):
    for row in rows:
        key_words = row.description
        key_words.update(row.named_entities['content'])
        near_trends = {}
        for topic in topics:
            common_words1 = topic.new_name.intersection(key_words)
            percent1 = len(common_words1)/len(topic.new_name)
            common_words = topic.name.intersection(key_words)
            percent = len(common_words) / len(topic.name)
            if percent >= 0.5 and percent1 >= 0.5:
                near_trends[topic] = len(common_words)
        max_topic = {key for key,value in near_trends.items() if value == max(near_trends.values())}
        for t in max_topic:
            if row not in t.news:
                t.news.append(row)
    return topics

def delete_duplicates(topics):
    to_remove = set()
    to_add = set()
    for t in topics:
        others = [to for to in topics if t != to]
        for o in others:
            if set(o.news) == set(t.news):
                to_remove.add(o)
                to_remove.add(t)
                if o not in to_add and t not in to_add:
                    new_topic = Topic(name=o.name | t.name, init_news=o.news)
                    to_add.add(new_topic)
    topics = [t for t in topics if t not in to_remove]
    topics.extend(to_add)
    return topics


db = input("DB name (default - day): ")
table = input("Table name (default - buffer): ")

if not db:
        db = "day"
if not table:
        table = "buffer"

c_descr = CorpusD(db, table)

c_descr.find_topics()
# write_topics("1-краткое.xlsx",c_descr.topics)
# write_topics("1-краткое.xls",c_descr.topics)
c_descr.delete_small()
# write_topics("2-краткое.xlsx", c_descr.topics)
# write_topics("2-краткое.xls", c_descr.topics)
c_descr.check_unique()
# write_topics("3-краткое.xlsx", c_descr.topics)
# write_topics("3-краткое.xls", c_descr.topics)
c_descr.topics = [t for t in c_descr.topics if t.isvalid()]
# write_topics("4-краткое.xlsx", c_descr.topics)
# write_topics("4-краткое.xls", c_descr.topics)
c_descr.final_delete()
# write_topics("5-краткое.xlsx", c_descr.topics)
# write_topics("5-краткое.xls", c_descr.topics)

c_content = CorpusC(db, table)

c_content.find_topics()
# write_topics("1-текст.xlsx", c_content.topics)
# write_topics("1-текст.xls", c_content.topics)
c_content.delete_small()
# write_topics("2-текст.xlsx", c_content.topics)
# write_topics("2-текст.xls", c_content.topics)
c_content.check_unique()
# write_topics("3-текст.xlsx", c_content.topics)
# write_topics("3-текст.xls", c_content.topics)
c_content.topics = [t for t in c_content.topics if t.isvalid()]
# write_topics("4-текст.xlsx", c_content.topics)
# write_topics("4-текст.xls", c_content.topics)

all_topics = c_descr.topics
all_topics.extend(c_content.topics)


write_topics("0.xlsx", all_topics)
# write_topics("0.xls", all_topics)

all_topics = unique(all_topics)

write_topics("2.xlsx", all_topics)
# write_topics("2.xls", all_topics)

all_topics = assign_news(all_topics, c_descr.data)

write_topics("4.xlsx", all_topics)
# write_topics("4.xls", all_topics)

all_topics = delete_duplicates(all_topics)

write_topics("5.xlsx", all_topics)
# write_topics("5.xls", all_topics)
