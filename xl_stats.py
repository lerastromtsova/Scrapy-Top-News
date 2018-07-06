import csv
import openpyxl


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

    for i, topic in enumerate(topics):
        if topic.subtopics:
            name = ''
            for s in topic.subtopics:
                name += f"{', '.join(s.name)} | {s.text_name} |"
        else:
            name = f"{' '.join(topic.name)} | {topic.text_name}"
        sheet.cell(row=i+1, column=1).value = name
        sheet.cell(row=i + 1, column=2).value = ', '.join(topic.new_name)
        sheet.cell(row=i + 1, column=3).value = ', '.join(topic.main_words)
        for j, doc in enumerate(topic.news):

            sheet.cell(row=i+1, column=j+4).value = f"{doc.id} | {doc.country} | {doc.url} | {doc.translated['title']} | " \
                                               f"{doc.translated['lead']} | " \
                                               f"{doc.translated['content']} | Из краткого: {doc.description} | Из текста: {doc.named_entities['content']}"


    wb.save(fname)

def write_news(fname, news):
    wb = openpyxl.Workbook()
    sheet = wb.active
    for i,doc in enumerate(news):
        sheet.cell(row=i+1, column=1).value = f"{doc.id} | {doc.country} | {doc.url}"
        sheet.cell(row=i + 1, column=2).value = f"{doc.translated['title']} | {doc.named_entities['title']}"
        sheet.cell(row=i + 1, column=3).value = f"{doc.translated['lead']} | {doc.named_entities['lead']}"
        sheet.cell(row=i + 1, column=4).value = f"{doc.translated['content']} | {doc.named_entities['content']}"

    wb.save(fname)