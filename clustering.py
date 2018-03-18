from gensim.models import Word2Vec
import sqlite3
from multiprocessing import cpu_count
from get_news import Corpus


corpus = Corpus(time='ANY')
model = Word2Vec(corpus, min_count=1, workers=cpu_count())
word_vectors = model.wv
del model

print(word_vectors)

