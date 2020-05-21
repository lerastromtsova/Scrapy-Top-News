from db_management import save_all
from newsapi import get_news
from datetime import datetime
from country_choices import short_codes as cc
from language_choices import short_codes as lc


def parametrize():
    parameters = dict()
    parameters['mode'] = input("Query type (top/everything): ")
    parameters['q'] = input("Query: ")
    if parameters['mode'] == 'everything':
        parameters['date_from'] = input("Date from (YYYY-MM-DD): ")
        parameters['date_to'] = input("Date to (YYYY-MM-DD): ")
        parameters['languages'] = input("Languages: ").split(', ')
        if parameters['languages'] == ['all']:
            parameters['languages'] = lc
    elif parameters['mode'] == 'top':
        parameters['countries'] = input("Countries: ").split(', ')
        if parameters['countries'] == ['all']:
            parameters['countries'] = cc
    else:
        raise Exception('No such query type!')
    return parameters


if __name__ == '__main__':
    parameters = parametrize()
    news = get_news(**parameters)
    db_name = datetime.today().strftime('db-%d-%m-%Y_%H-%M')
    save_all(news, db_name)
