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

    en_title_1 = Optional(str)
    en_title_2 = Optional(str)

    en_lead_1 = Optional(str)
    en_lead_2 = Optional(str)

    en_content_1 = Optional(str)
    en_content_2 = Optional(str)

    tokens_title = Optional(str)
    tokens_lead = Optional(str)
    tokens_content = Optional(str)

    nes_title = Optional(str)
    nes_lead = Optional(str)
    nes_content = Optional(str)

# implement later
# class Country(db.Entity):
#     name = Required(str)
#     capital = Required(str)


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


