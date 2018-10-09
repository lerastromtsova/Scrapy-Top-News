"""
This is where we find links between news
input: a list of news ['id','url','title','number','country','tokens','date'...]
output: a list of edges [(1,2),(2,4),...]
"""


def find_connection(data, m):
    edges = []
    for i in range(len(data)):
        for j in range(i+1,len(data)):
            text = data[i].tokens['content']
            text1 = data[j].tokens['content']

            common = set(text).intersection(set(text1))
            weight = len(common)

            if weight > int(m):
                edges.append({'from':i+1,'to':j+1,'weight':weight})

    return edges
