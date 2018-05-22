from trees import Corpus
from text_processing.translate import translate
from text_processing.preprocess import preprocess

corpus = Corpus("19_04_2018", "buffer", with_lead=True)

for row in corpus.data:
    title_tokens = []
    common_words = []

    eng_tit = translate(row.title)
    print(eng_tit)
    orig_tit = translate(eng_tit, arg=row.country)
    eng1_tit = translate(orig_tit)

    for tr in preprocess(eng_tit):
        if tr in preprocess(eng1_tit):
            title_tokens.append(tr)

    eng_lead = translate(row.lead)
    orig_lead = translate(eng_lead, arg=row.country)
    eng1_lead = translate(orig_lead)

    for tr in preprocess(eng_lead):
        if tr in preprocess(eng1_lead) and tr in title_tokens:
            common_words.append(tr)

    c = corpus.conn.cursor()
    c.execute(f"UPDATE {corpus.table} SET translated_title=(?), translated1_title=(?),"
              f"translated_lead=(?), translated1_lead = (?) WHERE reference=(?)",
              (eng_tit, eng1_tit, eng_lead, eng1_lead, row.url))
    corpus.conn.commit()
    print(common_words)
