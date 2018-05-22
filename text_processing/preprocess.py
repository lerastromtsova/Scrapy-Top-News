"""
This is where preprocessing happens.
input: text
output: preprocessed text (string)
"""
from nltk.corpus import wordnet as wn
import os
import nltk
import string

# STOP_PATH = '../../text_processing/stop-words.txt'
STOP_PATH = os.getcwd()+'/text_processing/stop-words.txt'

PUNKTS = ["''",'``','...','’','‘','-','“','"','—','”','–','–––','––']

with open(STOP_PATH,"r") as f:
    STOP_WORDS = f.read().split('\n')


def preprocess(text,with_uppercase=True):

    for p in PUNKTS:
        text = ' '.join(text.split(p))
    for p in string.punctuation:
        text = ' '.join(text.split(p))

    tokens = [wn.morphy(t) if wn.morphy(t) is not None else t for t in nltk.word_tokenize(text)]


    if with_uppercase:
        tokens = [t for t in tokens if (t.lower() not in STOP_WORDS or t == 'May')
                  and t not in PUNKTS and t not in string.punctuation
                  and len(t) > 1]

    else:
        tokens = [t.lower() for t in tokens if
                  (t.lower() not in STOP_WORDS or t =='May')
                  and t not in PUNKTS and t not in string.punctuation
                  and len(t)>1]
    return tokens