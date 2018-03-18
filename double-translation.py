from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from googletrans import Translator
import nltk
from nltk.corpus import wordnet as wn
import string
import csv
import json.decoder

Base = declarative_base()

engine = create_engine("sqlite:///db/mydatabase-2.db")
Base.metadata.create_all(bind=engine)


session = sessionmaker(bind=engine)
s = session()

connection = engine.connect()
result = connection.execute("select * from buffer")

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


for row in result:
    try:
        country = row[0]
        language = LANGS[country]
        title = row[1]
        content = row[2]

        if len(content)>=5000:
            cont1 = content[:5000]
            cont2 = content[5000:]
        else:
            cont1 = None
            cont2 = None

        if title:
            eng_tit = translate_to_en(title)
            print(f'English title: {eng_tit}')
            orig_tit = translate_to_orig(eng_tit, LANGS[country])
            eng1_tit = translate_to_en(orig_tit)

        tk1 = preprocess(eng_tit)
        tk2 = preprocess(eng1_tit)
        print(tk1)
        print(tk2)

        for word in tk1:
            if word in tk2:
                try:
                    frequencies[word]+=1
                except KeyError:
                    frequencies[word] = 1

        if not (cont1 and cont2):
            eng_cont = translate_to_en(content)
            orig_cont = translate_to_orig(eng_cont, LANGS[country])
            eng1_cont = translate_to_en(orig_cont)
        elif content:
            eng_cont1 = translate_to_en(cont1)
            orig_cont1 = translate_to_orig(eng_cont1, LANGS[country])
            eng1_cont1 = translate_to_en(orig_cont1)
            eng_cont2 = translate_to_en(cont2)
            orig_cont2 = translate_to_orig(eng_cont2, LANGS[country])
            eng1_cont2 = translate_to_en(orig_cont2)
            eng_cont = eng_cont1+eng_cont2
            eng1_cont = eng1_cont1+eng1_cont2

        tk1 = preprocess(eng_cont)
        tk2 = preprocess(eng1_cont)
        print(tk1)
        print(tk2)

        for word in tk1:
            if word in tk2:
                try:
                    frequencies[word]+=1
                except KeyError:
                    frequencies[word] = 1

        with open('freq.csv', 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for key, item in frequencies.items():
                writer.writerow([str(item),str(key)])
    except json.decoder.JSONDecodeError as err:
        print(err)

connection.close()

