import sqlite3
import re
from text_processing.translate import translate

conn = sqlite3.connect(f"db/day.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM buffer")

conn2 = sqlite3.connect("db/countries.db")
c2 = conn2.cursor()
c2.execute("SELECT * FROM countries")
all_rows = c2.fetchall()
COUNTRIES = [row[0] for row in all_rows]

STOP_PATH = './text_processing/stop-words.txt'
with open(STOP_PATH, "r") as f:
    STOP_WORDS = f.read().split('\n')

uppercase_words = []

rows = c.fetchall()
for i,row in enumerate(rows):
    print(i)
    print(row['translated_title'])
    print(row['nes_title'])
    print(row['translated_lead'])
    print(row['nes_lead'])
    print(row['translated'])
    print(row['nes_content'])


    for typ in ['title', 'lead', 'content']:
        uppercase_words = []
        uwords = set()
        if typ == 'content':
            text = row['translated']
        else:
            text = row[f'translated_{typ}']

        text = re.findall(r"[\w]+|[^\s\w]", text)
        for word in text:
            if word[0].isupper() and word.lower() not in STOP_WORDS:
                uppercase_words.append('Why did ' + word.lower() + ' say?')

        str_to_translate = '\n'.join(uppercase_words)

        with open("1.txt", "w") as f:
            f.write(str_to_translate)
        with open("1.txt", "r") as f:
            str_to_translate = f.read()

        eng = translate(str_to_translate, country_or_language='en')

        with open("2.txt", "w") as f:
            f.write(eng)
        with open("2.txt", "r") as f:
            eng = f.read()

        deu = translate(eng, country_or_language='de')

        with open("3.txt", "w") as f:
            f.write(deu)
        with open("3.txt", "r") as f:
            deu = f.read()

        eng1 = translate(deu, country_or_language='en')

        with open("4.txt", "w") as f:
            f.write(eng1)

        uppercase_words_en = eng.split('\n')
        uppercase_words_en1 = eng1.split('\n')
        uwords = set()

        for i in range(len(uppercase_words_en)):
            w = uppercase_words_en[i].split()[-2]
            w1 = uppercase_words_en1[i].split()[-2]

            if w and w1:

                if len(w) > 1 and w1[0].isupper() and w.lower() == w1.lower():
                    uwords.add(w1)
        print(uwords)