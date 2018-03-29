from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from googletrans import Translator
import nltk
from nltk.corpus import wordnet as wn
import string
import csv
import json.decoder
import pandas as pd

LANGS = {'Germany': 'de',
         'Russia': 'ru',
         'United States': 'en',
         'United Kingdom': 'en'}

with open('stop-words.txt', 'r') as stop_file:
    STOP_WORDS = stop_file.readlines()


t = Translator()

def translate_to_en(text):
    if "Краткое описание: " in text:
        text = text.split("Краткое описание: ")[1]
    return t.translate(text).text

def translate_to_orig(text, lang):
    return t.translate(text, dest=lang).text


def tokenize(text):
    tokens = nltk.word_tokenize(text)  # список слов в новости
    for i in range(len(tokens)):
        tokens[i] = tokens[i].lower()
        if wn.morphy(tokens[i]) is not None:
            tokens[i] = wn.morphy(tokens[i])  # используем morphy, чтобы убрать множ число и формы глаголов, а также понижаем регистр
    return tokens

def preprocess(text):
    punkts = ["''",'``','...','’','‘','-']
    tk = [x for x in tokenize(text) if x+'\n' not in STOP_WORDS
             and x not in string.punctuation and x not in punkts]
    return tk

frequencies = dict()
tks = list()
articles = list()
all_words = list()
bag = dict()


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

            if title:
                eng_tit = translate_to_en(str(title))
                orig_tit = translate_to_orig(str(eng_tit), language)
                eng1_tit = translate_to_en(str(orig_tit))

            tk1 = preprocess(str(eng_tit))
            tk2 = preprocess(str(eng1_tit))
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
            roww= [url, title, content, []]

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
                    if word not in all_words:
                        all_words.append(word)
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
    return all_words, frequencies


