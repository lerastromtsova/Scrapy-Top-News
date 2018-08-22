import csv
import openpyxl
from math import ceil
from document import COUNTRIES


def check_xl(nodes, all_links):
    file = csv.writer(open("t.csv", "w"), delimiter=',')

    for n in nodes:
        countries = {d.country for d in n.documents}
        row = [f"{n.name} | {countries}"]
        for k, m in all_links[n].items():
            row.append(f"{k.name} | {m} | {' '.join({d.country for d in k.documents})}")
            cd = set(n.documents).intersection(set(k.documents))
            cc = {d.country for d in cd}
            perc = len(cc)/len(countries)
            row.append(perc)
            row.append(cc)
            tex = ' | '.join([d.title for d in cd])
            row.append(tex)
        file.writerow(row)


def write_topics_with_freq(fname, nodes, with_children=False):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet['A1'] = 'Topic'
    sheet['B1'] = 'News'
    sheet['C1'] = 'Keywords'
    for i, n in enumerate(nodes):
        if with_children:
            text = ''

            if n.subtopics:
                for c in n.subtopics:

                    text += ' '.join(c.name)
                    text += ' | '
            else:
                if type(n.name) == 'str':
                    text = n.name
                else:
                    text = ' '.join(n.name)
        else:
            if type(n.name) == 'str':
                text = n.name
            else:
                text = ' '.join(n.name)
        freq_words = n.find_most_frequent(type="uppercase")
        for word, val in freq_words.items():
            t = f"|{word}:{val}|"
            text += t
        sheet.cell(row=i+2, column=1).value = text
        docs = n.documents
        for j,doc in enumerate(docs):
            sheet.cell(row=i+2, column=j+2).value = f"{doc.country} | {doc.translated['title']} | {doc.translated['lead']} | {doc.url} | {doc.translated['content']} | {doc.named_entities['title']} | {doc.named_entities['content']}"
    wb.save(fname)


def get_subtopics_string(node):
    if node.subtopics:
        return '|'.join([' '.join(s.name) for s in node.subtopics])
    return None


def write_topics_to_xl(fname, nodes, with_children=False):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet['A1'] = 'Topic'
    sheet['B1'] = 'News'
    sheet['C1'] = 'Keywords'
    for i, n in enumerate(nodes):
        if with_children:
            text = ''
            if n.subtopics:
                print(len(n.subtopics))
                for c in n.subtopics:
                    text += ' '.join(c.name)
                    text += ' | '
            else:
                if type(n.name) == 'str':
                    text = n.name
                else:
                    text = ' '.join(n.name)
        else:
            if type(n.name) == 'str':
                text = n.name
            else:
                text = ' '.join(n.name)
        sheet.cell(row=i+2, column=1).value = text
        docs = n.documents
        for j,doc in enumerate(docs):
            sheet.cell(row=i+2, column=j+2).value = f"{doc.country} | {doc.translated['title']} | {doc.translated['lead']} | {doc.url} | {doc.translated['content']} | {doc.named_entities['title']} | {doc.named_entities['content']}"
    wb.save(fname)


def write_tz(tree):
    wb = openpyxl.Workbook()
    sheet = wb.active
    for i,node in enumerate(tree.roots):
        texts = get_all_in_strings(node, [])
        for j, text in enumerate(texts):
            print(text)
            sheet.cell(row=i+1, column=j+1).value = text
    wb.save("tz-today.xlsx")


def get_all_in_strings(node, prev):
    prev.append(f"{node.name} | {len(node.documents)}")
    for ch in node.children:
        if ch.children:
            get_all_in_strings(ch, prev)
    return prev


def write_words_to_xl(fname, data):
    file = csv.writer(open(fname, "w"), delimiter=',')
    headers = ['Document', 'Deleted words']
    file.writerow(headers)

    for r in data:
        row = [r.translated, r.removed_words]
        file.writerow(row)


def write_start_words_to_xl(fname, data):
    file = csv.writer(open(fname, "w"))
    headers = ['Document', 'Deleted words']
    file.writerow(headers)

    for r in data:
        for key, ind in r.start_words.items():
            row = [key, ind]
            file.writerow(row)

def write_rows_content(fname, similarities):
    wb = openpyxl.Workbook()
    sheet = wb.active
    i = 1
    for row in similarities:
        j = 1
        # setlist = [doc.description for doc in row]
        setlist = [doc.named_entities['content'] for doc in row]
        topic = set.intersection(*setlist)
        sheet.cell(row=i,column=j).value = ' '.join(topic)
        for doc in row:
            j += 1
            sheet.cell(row=i,column=j).value = f"{doc.id} | {doc.country} | {doc.url} | {doc.translated['title']} | " \
                                               f"{doc.named_entities['title']} | {doc.translated['lead']} |" \
                                               f"{doc.translated['content']} | {doc.named_entities['content']}"
        i += 1
    wb.save(fname)

def write_rows_title(fname, similarities):
    wb = openpyxl.Workbook()
    sheet = wb.active
    i = 1
    for row in similarities:
        j = 1
        # setlist = [doc.description for doc in row]
        setlist = [{word.lower() for word in doc.tokens['title']} for doc in row]
        topic = set.intersection(*setlist)
        sheet.cell(row=i,column=j).value = ' '.join(topic)
        for doc in row:
            j += 1
            sheet.cell(row=i,column=j).value = f"{doc.id} | {doc.country} | {doc.url} | {doc.translated['title']} | " \
                                               f"{doc.named_entities['title']} | {doc.translated['lead']} |" \
                                               f"{doc.translated['content']} | {doc.named_entities['content']}"
        i += 1
    wb.save(fname)

def write_topics(fname, topics):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.cell(row=1, column=1).value = "# of news"
    sheet.cell(row=1, column=2).value = "# of words (without FIO)"
    sheet.cell(row=1, column=3).value = "# of words (with FIO)"
    sheet.cell(row=1, column=4).value = "# of countries"
    sheet.cell(row=1, column=5).value = "# of words with small letter"
    sheet.cell(row=1, column=6).value = "# of unique words"
    sheet.cell(row=1, column=7).value = "# of FIO"
    sheet.cell(row=1, column=8).value = "Method of check"

    sheet.cell(row=1, column=9).value = "Topic"
    sheet.cell(row=1, column=10).value = "Unique"
    sheet.cell(row=1, column=11).value = "Check"
    sheet.cell(row=1, column=12).value = "Most frequent"
    sheet.cell(row=1, column=13).value = "50% frequent"
    sheet.cell(row=1, column=14).value = "What"
    sheet.cell(row=1, column=15).value = "What2"
    sheet.cell(row=1, column=16).value = "Common in descriptions"
    sheet.cell(row=1, column=17).value = "Common in text"
    sheet.cell(row=1, column=18).value = "News"

    counts = [0]*7

    for i, topic in enumerate(topics):
        if topic.subtopics:
            name = ''
            for s in topic.subtopics:
                name += f"{', '.join(s.name)} | {s.text_name} |"
        else:
            name = f"{', '.join(topic.name)} | {topic.text_name}"

        sheet.cell(row=i + 3, column=1).value = len(topic.news)

        counts[0] += 1

        without_fio = []
        count_fio = 0
        for word in topic.name:
            parts = word.split()
            for w in parts:
                without_fio.append(w)
            if len(parts) >= 2:
                count_fio += 1

        if without_fio:
            sheet.cell(row=i + 3, column=2).value = len(without_fio)
            counts[1] += 1
        if topic.name:
            sheet.cell(row=i + 3, column=3).value = len(topic.name)
            counts[2] += 1

        countries = [t for t in topic.name if t in COUNTRIES]
        if countries:
            sheet.cell(row=i + 3, column=4).value = len(countries)
            counts[3] += 1
        lower = [t for t in topic.name if t[0].islower()]
        if lower:
            sheet.cell(row=i + 3, column=5).value = len(lower)
            counts[4] += 1
        if topic.new_name:
            sheet.cell(row=i + 3, column=6).value = len(topic.new_name)
            counts[5] += 1
        if count_fio:
            sheet.cell(row=i + 3, column=7).value = count_fio
            counts[6] += 1

        sheet.cell(row=i + 3, column=8).value = " ".join(topic.method)

        sheet.cell(row=i + 3, column=9).value = name
        sheet.cell(row=i + 3, column=10).value = ', '.join(topic.new_name)
        sheet.cell(row=i + 3, column=11).value = ', '.join(topic.main_words)
        if topic.frequent:
            sheet.cell(row=i + 3, column=12).value = ', '.join(topic.frequent)
            sheet.cell(row=i + 3, column=13).value = ', '.join(topic.frequent[:ceil(len(topic.frequent) / 2)])
        else:
            sheet.cell(row=i + 3, column=12).value = ', '.join(topic.most_frequent())
            sheet.cell(row=i + 3, column=13).value = ', '.join(topic.most_frequent()[:ceil(len(topic.frequent) / 2)])
        sheet.cell(row=i + 3, column=14).value = ', '.join(topic.objects)
        sheet.cell(row=i + 3, column=15).value = ', '.join(topic.obj)
        sheet.cell(row=i + 3, column=16).value = ', '.join(topic.news[0].description.intersection(topic.news[1].description))
        sheet.cell(row=i + 3, column=17).value = ', '.join(topic.news[0].named_entities['content'].intersection(topic.news[1].named_entities['content']))

        for j, doc in enumerate(topic.news):

            sheet.cell(row=i + 3, column=j+18).value = f"{doc.id} | {doc.country} | {doc.url} | {doc.translated['title']} | " \
                                               f"{doc.translated['lead']} | " \
                                               f"{doc.translated['content']} | Из краткого: {doc.description} | Из текста: {doc.named_entities['content']}"

    for n in range(7):
        sheet.cell(row=2, column=n+1).value = counts[n]

    wb.save(fname)

def write_news(fname, news):
    wb = openpyxl.Workbook()
    sheet = wb.active
    for i,doc in enumerate(news):
        sheet.cell(row=i + 1, column=1).value = f"{doc.id} | {doc.country} | {doc.url}"
        sheet.cell(row=i + 1, column=2).value = f"{doc.translated['title']} | {doc.named_entities['title']}"
        sheet.cell(row=i + 1, column=3).value = f"{doc.translated['lead']} | {doc.named_entities['lead']}"
        sheet.cell(row=i + 1, column=4).value = f"{doc.translated['content']} | {doc.named_entities['content']}"

    wb.save(fname)