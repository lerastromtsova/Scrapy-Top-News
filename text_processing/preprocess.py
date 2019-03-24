"""
This is where preprocessing happens.
input: text
output: preprocessed text (string)
"""
from nltk.corpus import wordnet as wn
import os
import nltk
import string
from text_processing.translate import translate
import re
import sqlite3
from copy import copy

# STOP_PATH = '../../text_processing/stop-words.txt'
STOP_PATH = os.getcwd()+'/text_processing/stop-words.txt'
PUNKTS = ["''",'``','...','’','‘','-','“','"','—','”','–','–––','––', " | "]
SYM_MAP = {'â': 'a', 'Ç': 'C', 'ç': 'c', 'Ğ': 'g', 'ğ': 'g', 'İ': 'I', 'î': 'i', 'Ö': 'O', 'ö': 'oe',
           'Ş': 'S', 'ş': 's', 'Ü': 'U', 'ü': 'u', 'é': 'e', 'à': 'a', 'è': 'e', 'û': 'u', 'ô': 'o', 'œ': 'o',
           'ñ': 'n', 'á': 'a', 'í': 'i', 'ú': 'u', 'č': 'c', 'ć': 'c', 'ů': 'u', 'ey': 'ei', 'yo': 'e',
           'ye': 'e', 'yu': 'iu', 'ya': 'ia'}


def unite_countries_in_topic_names(name):
    to_remove = set()
    to_add = set()
    for word in name:
        for word2 in name:
            d1 = unite_countries_in([word, word2])
            if d1 != [word, word2]:
                to_remove.add(word)
                to_remove.add(word2)
                to_add.add(d1[0])
        if word.upper() == 'UNITED':
            to_remove.add(word)
    name -= to_remove
    name |= to_add
    return name

def unite_countries_in(data):
    conn = sqlite3.connect("db/countries.db")
    c = conn.cursor()
    c.execute("SELECT * FROM countries")
    all_rows = c.fetchall()
    to_remove = set()
    to_add = set()

    def unite_in_list(data):
        for i in range(len(data)-1):
            ent = data[i]
            for row in all_rows:
                low = [w.lower() for w in row if w is not None]

                if ent:
                    if ent.lower() in low and ent != row[0]:
                        data[i] = row[0]
                    elif (ent+' '+data[i+1]).lower() in low:
                        data[i] = row[0]
                        data[i+1] = ''
                if len(ent.lower().split()) > 1 and ent != row[0]:
                    for e in ent.lower().split():
                        if e in low:
                            data[i] = row[0]
        data = [w for w in data if w]
        return data

    if isinstance(data, set):
        for ent in data:
            for row in all_rows:
                low = [w.lower() for w in row if w is not None]

                if ent:
                    if ent.lower() in low and ent != row[0]:

                        to_remove.add(ent)
                        to_add.add(row[0])
                    if len(ent) <= 1:
                        to_remove.add(ent)

                if len(ent.lower().split()) > 1 and ent != row[0]:
                    for e in ent.lower().split():
                        if e in low:
                            to_remove.add(ent)
                            to_add.add(row[0])
        data = (data - to_remove) | to_add

    elif isinstance(data, list):
        data = unite_in_list(data)

    elif isinstance(data, str):
        data = re.findall(r"[\w]+|[^\s\w]", data)
        data = unite_in_list(data)
        data = ' '.join(data)

    return data


def replace_special_symbols(text):
    new_text = copy(text)
    # for i in range(len(new_text)-1):
    #     if new_text[i] == new_text[i+1] and new_text[i].islower():
    #         SYM_MAP[new_text[i]*2] = new_text[i]

    for key, value in SYM_MAP.items():
            new_text = new_text.replace(key, value)
    return new_text


replace_double = {}


def replace_double_letters(tokens):
    to_add = set()
    for token in tokens:
        if token in replace_double.keys():
            to_add.add(replace_double[token])
        else:
            if not token.isupper() and token[0].isupper():
                token_copy = token
                for i in range(len(token)-1):
                    if token[i] == token[i-1]:
                        token_copy = token_copy.replace(token[i]+token[i-1], token[i])
                if token_copy != token:
                    replace_double[token] = token_copy
                    to_add.add(token_copy)
    tokens.update(to_add)
    return tokens


with open(STOP_PATH, "r") as f:
    STOP_WORDS = f.read().split('\n')


def preprocess(text, with_uppercase=True):

    for p in PUNKTS:
        text = ' '.join(text.split(p))
    for p in string.punctuation:
        text = ' '.join(text.split(p))

    tokens = [wn.morphy(t) if wn.morphy(t) is not None else t for t in nltk.word_tokenize(text)]

    if with_uppercase:
        tokens = [t for t in tokens if (t.lower() not in STOP_WORDS)
                  and t not in PUNKTS and t not in string.punctuation
                  and len(t) > 1]

    else:
        tokens = [t.lower() for t in tokens if
                  (t.lower() not in STOP_WORDS)
                  and t not in PUNKTS and t not in string.punctuation
                  and len(t) > 1]

    for key, value in SYM_MAP.items():
        tokens = [t.replace(key, value) for t in tokens]

    # to_add = []
    # to_remove = []
    # for i in range(len(tokens)-1):
    #     if tokens[i].isdigit():
    #         if tokens[i + 1].isdigit():
    #             to_add.append(tokens[i] + tokens[i + 1])
    #             to_remove.append(tokens[i])
    #             to_remove.append(tokens[i + 1])
    #
    # tokens.extend(to_add)
    # tokens = [t for t in tokens if t not in to_remove]

    return tokens


conn = sqlite3.connect("db/entities.db")
c = conn.cursor()
c.execute("SELECT * FROM entities")
all_rows = c.fetchall()
DEFINITELY_ENTITIES = [row[0] for row in all_rows]


def find_entities(sentence):

    uppercase_words = []
    named_entities = set()

    for word in sentence:
        if word in DEFINITELY_ENTITIES:
            named_entities.add(word)
        elif word[0].isupper():
            if word.lower() not in STOP_WORDS:
                uppercase_words.append('Why did ' + word.lower() + ' say?')

    str_to_translate = '\n'.join(uppercase_words)

    eng = translate(str_to_translate, country_or_language='en')
    deu = translate(eng, country_or_language='de')
    eng1 = translate(deu, country_or_language='en')

    eng = eng.split('\n')
    eng1 = eng1.split('\n')

    for i in range(len(eng)):
        if eng[i]:
            word = eng[i].split()[-2]
            word1 = eng1[i].split()[-2]
            if len(word) > 1 and word1[0].isupper() and word.lower() == word1.lower():
                named_entities.add(word1)
                c.execute("INSERT OR REPLACE INTO entities (name) VALUES (?)", (word1, ))
                # print(word1)

    conn.commit()

    return named_entities


def check_first_entities(list_of_ents):
    uppercase_words = []
    named_entities = {}
    for word in list_of_ents:
        uppercase_words.append('Why did ' + word.lower() + ' say?')
    str_to_translate = '\n'.join(uppercase_words)

    eng = translate(str_to_translate, country_or_language='en')
    deu = translate(eng, country_or_language='de')
    eng1 = translate(deu, country_or_language='en')

    eng = eng.split('?\n')
    eng1 = eng1.split('?')

    for i in range(len(eng)):
        if eng[i]:
            word = eng[i].split()[-2]
            word1 = eng1[i].split()[-2]
            if len(word) > 1 and word1[0].isupper() and word.lower() == word1.lower():
                named_entities[word1] = True
            elif word1[0].islower() and word.lower() == word1.lower():
                named_entities[word1] = False
    return named_entities


def split_into_paragraphs(text):
    return text.split('\n')

def split_into_sentences(paragraph):
    sentenceEnders = re.compile('[.!?]')
    sentenceList = sentenceEnders.split(paragraph)
    return sentenceList
