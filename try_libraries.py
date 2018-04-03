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
# def extract_entities(text):
#     nes = []
#     for sent in nltk.sent_tokenize(text):
#         for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
#             try:
#                 flat_tree = ' '.join(chunk.pprint().split())
#                 if 'NE' in flat_tree:
#                     nes.append(flat_tree)
#             except AttributeError:
#                 pass
#
#     return nes

#print(extract_entities(text))
#print('\n'.join(exm.split('.')))
#print(extract_entities(exm))

text1 = 'ТАСС, 3 апреля. 01.02.2018 Российская актриса Мария Аронова перед 03.02.2018 спектаклем "Маленькие комедии" в Сургуте (Ханты-Мансийский автономный округ - Югра) сообщила зрителям о невыплате гонорара. Ролик с ее заявлением появился в социальной сети YouTube.'
text2 = 'В документе говорится, что название «предположительное». 23 Января 2017 Учредительный съезд партии должен пройти 19 мая 2018 года. '
text3 = 'В сентябре 2017 года в Госдепартаменте отметили, что американская сторона не желает продолжать политику «око за око» в отношениях с Россией.'
text4 = 'Запланировали съезд партии на 9 мая. Поскольку название у нас утащили, до съезда будет рабочее название'

def ismonth(str):
    MONTHS = ['january','february','march','april','may','june','july','august','september','october','november','december',
              'jan','feb','mar','apr','jun','jul','aug','sept','oct','nov','dec']
    STR_MONTHS = ['01','02','03','04','05','06','07','08','09','10','11','12']
    if str in MONTHS or str is STR_MONTHS:
        return True
    else:
        return False

def isyear(str):
    if str.isdigit() and len(str)==4:
        return True
    else:
        return False

def isday(str):
    if str.isdigit() and (len(str)==2 or len(str)==1):
        return True
    else:
        return False

from datetime import datetime
now = datetime.now()

def process_dates(text):
    tks = get_useful(text,'ru')
    dates = []
    for i,t in enumerate(tks):
        try:
            dt = datetime.strptime(t,'%m/%d/%Y')
            date = ((str(dt.day),str(dt.month),str(dt.year)))
            dates.append(date)
        except ValueError:
            pass
        if ismonth(t):
            year = None
            month = t
            day = None

            try:
                if isyear(tks[i+2]):
                    year = tks[i+2]
                if isday(tks[i+2]):
                    day = tks[i+2]
            except KeyError:
                pass
            try:
                if isyear(tks[i-2]):
                    year = tks[i-2]
                if isday(tks[i-2]):
                    day = tks[i-2]
            except KeyError:
                pass

            try:
                if isyear(tks[i+1]):
                    year = tks[i+1]
                if isday(tks[i+1]):
                    day = tks[i+1]
            except KeyError:
                pass
            try:
                if isyear(tks[i-1]):
                    year = tks[i-1]
                if isday(tks[i-1]):
                    day = tks[i-1]
            except KeyError:
                pass



            if not year:
                year = now.year
            if not day:
                day = now.day

            dates.append((day,month,year))
    print(dates)
    return dates




def get_useful(text,orig):
    en_text = translate(text)
    or_text = translate(en_text,orig)
    en1_text = translate(or_text)
    print(en_text)
    print(en1_text)
    return [t for t in preprocess(en_text).split() if t in preprocess(en1_text).split()]

process_dates(text1)
process_dates(text2)
process_dates(text3)
process_dates(text4)