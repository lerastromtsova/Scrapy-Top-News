from double_translation import get_data
import json
import csv
import ast


a1, f1, r1 = get_data("day", "buffer","1")
with open('c1.json', 'w') as fp:
    json.dump(f1, fp, ensure_ascii=False)

a2, f2, r2 = get_data("week", "buffer","2")
with open('c4.json', 'w') as fp:
    json.dump(f2, fp, ensure_ascii=False)

a3, f3, r3 = get_data("month","buffer","3")
with open('c3.json', 'w') as fp:
    json.dump(f3, fp, ensure_ascii=False)


a4, f4, r4 = get_data("mydatabase-2","buffer","4")
with open('c4.json', 'w') as fp:
    json.dump(f4, fp, ensure_ascii=False)
with open('a4.json','w') as fp:
    json.dump(a4, fp, ensure_ascii=False)


"""


f = list()
for i in range(1,5):
 f.append(json.load(open(f'c{i}.json')))

#all_words = json.load(open('a4.json'))
file = csv.writer(open("test.csv", "w"))

articles = dict()
corpuses = dict()
all = dict()
all_words = list()

for corpus in f:
 for key, words in corpus.items():
     for word in words:
         all_words.append(word)

art_list = list()
by_article = list()
by_corpus = list()

for e,word in enumerate(all_words):
    by_article.append(list())
    articles[word] = 0
    corpuses[word] = []
    for i, c in enumerate(f):
        for key, words in c.items():
            if word in words.keys():
                articles[word]+=1
                if i not in corpuses[word]:
                    corpuses[word].append(i)
                by_article[e].append(words[word])
            else:
                by_article[e].append(0)


for i, corp in enumerate(f):
    for key, words in corp.items():
        if 'https://' in key:
            art_list.append(key)


rows = [[key, item] for key, item in articles.items()]

for row in rows:
 try:
     row.append(len(corpuses[row[0]]))
 except KeyError:
     row.append(0)

for k, row in enumerate(rows):
 row+=by_article[k]

headers = ['Word', 'Articles','DB']+art_list
file.writerow(headers)

file.writerows(rows)
"""
