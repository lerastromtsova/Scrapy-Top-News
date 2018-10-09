from get_news import Corpus
from find_connection import find_connection
from draw_graph import draw_graph_only_news


if __name__ == '__main__':
    db = input("DB name (default - day): ")
    table = input("Table name (default - buffer): ")
    m = input("Weight: ")

    if not db:
        db = "day"
    if not table:
        table = "buffer"
    if not m:
        m = 4

    c = Corpus(db, table)
    edges = find_connection(c.data, m)
    draw_graph_only_news(c.data, edges, m, f"{db}-{m}", "без связей внутри")