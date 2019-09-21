from pony.orm import *
from datetime import datetime


# set_sql_debug(True)

db = Database()
db.bind(provider='sqlite', filename=f'db/news.db', create_db=True)


class News(db.Entity):

    country = Optional(str)
    reference = Optional(str)
    date = Optional(datetime, 6)

    title = Optional(str)
    lead = Optional(str)
    content = Optional(str)

    translated = Optional(str)
    translated1 = Optional(str)

    translated_lead = Optional(str)
    translated1_lead = Optional(str)

    translated_title = Optional(str)
    translated1_title = Optional(str)

    tokens_title = Optional(str)
    tokens_lead = Optional(str)
    tokens_content = Optional(str)

    nes_title = Optional(str)
    nes_lead = Optional(str)
    nes_content = Optional(str)


db.generate_mapping(create_tables=True)


@db_session
def create_news_item(**kwargs):
    for key, value in kwargs.items():
        if value is None:
            kwargs[key] = ' '
    news_item = News(**kwargs)


@db_session
def update_news_item(**kwargs):
    for key in kwargs:
        News[kwargs['id']].key = kwargs[key]


@db_session
def delete_news_item(id):
    News[id].delete()


def save_all(news):
    for country, news_list in news.items():
        for new in news_list:
            create_news_item(
                country=country,
                reference=new['url'],
                date=new['publishedAt'].split('T')[0],
                title=new['title'],
                lead=new['description'],
                content=new['content']
            )
