"""
This is where we find links between news
input: a list of news ['id','url','title','number','country','tokens','date'...]
output: a list of edges [(1,2),(2,4),...]
"""


def find_connection(data):
    edges = []
    for i in range(len(data)):
        for j in range(i+1,len(data)):
            print(data[i][5])
            print(data[j][5])
            weight = 0
            for token in data[i][5]:
                if token in data[j][5]:
                    weight+=1
            if weight>0:
                edges.append((i,j,weight))
    return edges