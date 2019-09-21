from db_management import save_all
from newsapi import get_news


def parametrize():
    parameters = dict()
    parameters['mode'] = input("Query type (top/everything): ")
    parameters['q'] = input("Query: ")
    if parameters['mode'] == 'everything':
        parameters['date_from'] = input("Date from (YYYY-MM-DD): ")
        parameters['date_to'] = input("Date to (YYYY-MM-DD): ")
        parameters['languages'] = input("Languages: ").split(', ')
    elif parameters['mode'] == 'top':
        parameters['countries'] = input("Countries: ").split(', ')
    else:
        raise Exception('No such query type!')
    return parameters


if __name__ == '__main__':
    parameters = parametrize()
    news = get_news(**parameters)
    save_all(news)
