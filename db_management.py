from pony.orm import *
from datetime import datetime


set_sql_debug(True)

db = Database()
db.bind(provider='sqlite', filename='db/day12.sqlite', create_db=True)


class News(db.Entity):

    country = Required(int, fk_name='Country')
    reference = Required(str)
    date = Required(datetime, 6)

    title = Required(str)
    lead = Required(str)
    content = Required(str)

    en_title_1 = Required(str)
    en_title_2 = Required(str)
    en_lead_1 = Required(str)
    en_lead_2 = Required(str)
    en_content_1 = Required(str)
    en_content_2 = Required(str)

    tokens_title = Required(str)
    tokens_lead = Required(str)
    tokens_content = Required(str)

    nes_title = Required(str)
    nes_lead = Required(str)
    nes_content = Required(str)


class Country(db.Entity):
    name = Required(str)
    capital = Required(str)


db.generate_mapping(create_tables=True)


@db_session
def create_news_item(**kwargs):
    print(kwargs['country'])
    country = Country.get(name=kwargs['country'])
    print(country.id)
    kwargs['country'] = country

    news_item = News(**kwargs)


create_news_item(country="Germany",
                 reference="http://")

