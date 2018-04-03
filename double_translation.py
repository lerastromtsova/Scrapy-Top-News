from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
import csv
import json.decoder
from scrapnews.translate import translate
from scrapnews.preprocess import preprocess
from gensim.corpora import Dictionary
from pandas import DataFrame, Series
from gensim.matutils import corpus2csc

LANGS = {'Germany': 'de',
         'Russia': 'ru',
         'United States': 'en',
         'United Kingdom': 'en'}

def translate_to_en(text):
    if len(text)>5000:
        translate_to_en(text[:5000])
    if "Краткое описание: " in text:
        text = text.split("Краткое описание: ")[1]
    return translate(text)

def translate_to_orig(text, lang):
    if len(text)>5000:
        translate_to_orig(text[:5000],lang)
    return translate(text, language=lang)


texts = []

#
# def get_corpus(db):
#     conn = sqlite3.connect(f"db/{db}.db")
#     c = conn.cursor()
#     c.execute("SELECT * FROM buffer")
#
#     dct = Dictionary()
#     news = c.fetchall()
#
#     for item in news:
#         try:
#             en_title = translate_to_en(item[1])
#             en_content = translate_to_en(item[2])
#
#             orig_title = translate_to_orig(en_title,LANGS[item[0]])
#             orig_content = translate_to_orig(en_content,LANGS[item[0]])
#
#             en1_title = translate_to_en(orig_title)
#             en1_content = translate_to_en(orig_content)
#
#             text = en_title+' '+en_content
#             text2 = en1_title+' '+en1_content
#             text = preprocess(text).split()
#             text2 = preprocess(text2).split()
#
#             texts.append(text)
#
#             common = set(text).intersection(set(text2))
#
#             dct.add_documents([list(common)])
#         except json.decoder.JSONDecodeError as err:
#             pass
#         return dct
#
# dct_month = get_corpus("month")
# dct_week = get_corpus("week")
# dct_day = get_corpus("day")
#
# dct = Dictionary(texts)
# bow_corpus = [dct.doc2bow(line) for line in texts]
# term_doc_mat = corpus2csc(bow_corpus)




# def write_to_csv(dc,name):
#     d2b = []
#     file = csv.writer(open(f"{name}.csv", "w", encoding="utf_8_sig"))
#     for t in texts:
#         file.writerow(dc.doc2bow(t))
#     i2t = []
#     for i in range(len(dc)):
#         file.writerow((i,dc[i]))
#
#     freq = []





    #df = DataFrame([[word[1] for word in dc.doc2bow(t)] for t in texts],columns=[dc[i] for i in range(len(dc))],index=[t for t in texts])
    # for i, t in enumerate(texts):
    #     d2b = dc.doc2bow(t) #[(1,2)(9,0)]
    #     row = Series(index=t,[[word[1] for word in d2b])
    #     for word in d2b:
    #         w = dc[word[0]]
    #         row[w] = []
    #         f = word[1]
    #         row[w].append([t, f])
    #     print(row)
    #     d = DataFrame(row)
    #     print(d)
    #     df.append(d).fillna(0)
    # print(df)
    # df.to_csv(f"{name}.csv")

# write_to_csv(dct_day,"day")
# write_to_csv(dct_month,"month")
# write_to_csv(dct_week,"week")

frequencies = {}
all_words = set()
articles = []

def get_data(db, table,n):
    file = csv.writer(open(f"articles{n}.csv", "w", encoding="utf_8_sig"))
    success = 0
    error = 0
    Base = declarative_base()

    engine = create_engine("sqlite:///db/"+db+".db")
    Base.metadata.create_all(bind=engine)

    session = sessionmaker(bind=engine)
    s = session()

    connection = engine.connect()
    result = connection.execute("select * from "+table)

    for row in result:
        try:
            country = row[0]
            language = LANGS[country]
            title = row[1]
            content = row[2].replace("\n"," ")
            print(content)
            contents = [content[i:i+1500] for i in range(0, len(content), 1500)]
            url = row[3]

            tk2 = ''

            if title:
                eng_tit = translate_to_en(str(title))
                orig_tit = translate_to_orig(str(eng_tit), language)
                eng1_tit = translate_to_en(str(orig_tit))
                tk2 = preprocess(str(eng1_tit))

            tk1 = preprocess(str(eng_tit))

            eng_cont_all = ""
            orig_cont_all = ""
            eng1_cont_all = ""
            for cont in contents:
                eng_cont = translate_to_en(str(cont))
                orig_cont = translate_to_orig(str(eng_cont), language)
                eng1_cont = translate_to_en(str(orig_cont))
                eng_cont_all += str(eng_cont)
                orig_cont_all += str(orig_cont)
                eng1_cont_all += str(eng1_cont)

            tk1 += preprocess(str(eng_cont_all))
            tk2 += preprocess(str(eng1_cont_all))
            roww = [url, title, content, []]

            for word in tk1:
                if word in tk2:
                    roww[3].append(word)
                    try:
                        frequencies[url][word] += 1
                    except KeyError:
                        try:
                            frequencies[url].update({word: 1})
                        except KeyError:
                            frequencies[url] = {word: 1}
                    all_words.add(word)

            file.writerow(roww)
            articles.append([eng_tit,eng_cont_all,url])


            print("Success ",row)
            success += 1



        except json.decoder.JSONDecodeError as err:
            print("Error ", row)
            error += 1

    connection.close()
    """for word in all_words:
        for art in articles:
            print(art)
            if word in art:
                print(word)
                try:
                    bag[art][word] += 1
                except KeyError:
                    bag[art] = {word: 1}"""
    print(success,error)
    return all_words, frequencies, result


