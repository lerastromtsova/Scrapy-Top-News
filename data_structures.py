from text_processing.preprocess import preprocess, find_entities, split_into_paragraphs, split_into_sentences
from text_processing.translate import translate
import sqlite3
import re

conn = sqlite3.connect("db/countries.db")
c = conn.cursor()
c.execute("SELECT * FROM countries")
COUNTRIES_ROWS = c.fetchall()


def replace_countries(text, orig_country):
    new_text = set()
    for word in text:
        for row in COUNTRIES_ROWS:
            low = [w.lower() for w in row if w is not None]
            if word.lower() in low:
                new_text.add(row[0])
            elif word.lower() == 'state' and orig_country == 'United Kingdom':
                new_text.add("UNITED STATES")
            else:
                new_text.add(word)
    return new_text


class Sentence:

    def __init__(self, raw_text, country, need_translation, need_tokenization):

        if need_translation and need_tokenization:

            transl_text = translate(raw_text)
            orig_text = translate(transl_text, country)
            double_transl_text = translate(orig_text)
            self.tokens = {word for word in preprocess(transl_text) if word in preprocess(double_transl_text)}
        elif need_tokenization:
            self.tokens = {preprocess(raw_text)}
        else:
            self.tokens = set(raw_text)
        self.tokens = replace_countries(self.tokens, country)
        self.named_entities = find_entities(self.tokens)
        self.named_entities = replace_countries(self.named_entities, country)


class Paragraph:

    def __init__(self, sentences):
        self.sentences = sentences


class Document:

    def __init__(self, id, row, conn, table):

        types = ('title','lead','content')
        self.id = id
        self.raw = row

        self.country = row['country']
        self.date = row['date']
        self.url = row['reference']
        self.paragraphs = dict.fromkeys(types, [])

        for type in types:
                paragraphs = split_into_paragraphs(row[type])
                for paragraph in paragraphs:
                    sentences = split_into_sentences(paragraph)
                    print(sentences)
                    sentObjs = []
                    for sentence in sentences:
                        sentObj = Sentence(sentence, self.country, True, True)
                        sentObjs.append(sentObj)
                    parObj = Paragraph(sentObjs)
                    self.paragraphs[type].append(parObj)


class Corpus:

    def __init__(self, db, table):

        self.db = db
        self.table = table
        self.conn = sqlite3.connect(f"db/{db}.db")
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.c.execute("SELECT * FROM " + table)
        self.topics = []
        self.data = []
        self.trends = []
        self.similarities = []
        self.frequencies = {}

        raw_data = self.c.fetchall()

        for i, row in enumerate(raw_data):
            doc = Document(i, row, self.conn, table)
            self.data.append(doc)

        for doc in self.data:
            for paragraph in doc.paragraphs['content']:
                for sentence in paragraph.sentences:
                    print(sentence.named_entities)


if __name__ == '__main__':

    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"

    c = Corpus(db, table)