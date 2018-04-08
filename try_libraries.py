from scrapnews.translate import translate
from scrapnews.preprocess import preprocess
import sqlite3
import nltk

from nltk.tag.stanford import StanfordNERTagger

# conn = sqlite3.connect('db/week.db')
# c = conn.cursor()
# c.execute("SELECT * FROM buffer")
# news = c.fetchall()
# #examples = [translate(item[2]) for item in news]
# exm = translate(news[0][2])
#
# exm_ch = u"国国家元首、政府首脑和国际组织负责人，集体会见论坛的理事，并且同与会的中外企业家代表座谈。这是习近平主席作为中国国家主席第三次出席博鳌亚洲论坛年会，充分体现了习近平主席本人和中国政府对论坛的高度重视和大力支持。王毅表示，本次年会以“开放创新的亚洲，繁荣发展的世界”为主题。来自各国的2000多位各界嘉宾将汇聚一堂，共商合作共赢大计，为亚洲和世界提供“博鳌智慧”，贡献“博鳌力量”"
# en_exm = translate(exm_ch)
# print("\n".join(en_exm.split('.')))
# exm_ch = translate(exm_ch,language='ja')
# en1_exm = translate(exm_ch)
# print("\n".join(en1_exm.split('.')))
#
# text = set(en_exm.split()).union(set(en1_exm.split()))
# text = ' '.join(text)
#
def extract_entities(text):
    nes = []
    for sent in nltk.sent_tokenize(text):
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
            try:
                flat_tree = ' '.join(chunk.pprint().split())
                if 'NE' in flat_tree:
                    nes.append(flat_tree)
            except AttributeError:
                pass

    return nes

#print(extract_entities(text))
#print('\n'.join(exm.split('.')))
#print(extract_entities(exm))

text1 = 'ТАСС, 3 апреля. 01.02.2018 Российская актриса Мария Аронова перед 03.02.2018 спектаклем "Маленькие комедии" в Сургуте (Ханты-Мансийский автономный округ - Югра) сообщила зрителям о невыплате гонорара. Ролик с ее заявлением появился в социальной сети YouTube.'
text2 = 'В документе говорится, что название «предположительное». 23 Января 2017 Учредительный съезд партии должен пройти 19 мая 2018 года. '
text3 = 'В сентябре 2017 года в Госдепартаменте отметили, что американская сторона не желает продолжать политику «око за око» в отношениях с Россией.'
text4 = 'Запланировали съезд партии на 9 мая. Поскольку название у нас утащили, до съезда будет рабочее название'
