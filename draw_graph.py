import plotly.tools as tools
import plotly.plotly as py
from plotly.graph_objs import *
import networkx as nx
from get_news import Topnews, Corpus
from datetime import datetime

tools.set_credentials_file(username='v.stromtsova@yandex.ru', api_key='1AiEemPFWZeSclPX2ZQM')
py.sign_in("valeria19988", "1AiEemPFWZeSclPX2ZQM")

COLORS = {'Australia': 'dusty rose',
          'Argentina': 'blue',
          'Armenia': 'red',
          'Belarus': 'green',
          'Bulgary': 'brown',
          'Brazil': 'sienna',
          'Great Britain': 'black',
          'United Kingdom': 'black',
          'Georgia': 'dark gray',
          'Germany': 'olive',
          'Greece': 'beige',
          'India': 'purple',
          'Italy': 'wheat',
          'Kazakhstan': 'khaki',
          'Mexica': 'golden',
          'Canada': 'tomato',
          'Netherlands': 'coral',
          'Portugal': 'forest green',
          'Russia': 'salmon',
          'Romania': 'hot pink',
          'USA': 'fuchsia',
          'United States': 'fuchsia',
          'Uzbekistan': 'medium spring green',
          'Singapore': 'orange',
          'Turkey': 'plum',
          'Ukraine': 'indigo',
          'Finland': 'maroon',
          'France': 'crimson',
          'Czech Republic': 'silver',
          'Switzerland': 'goldenrod',
          'Estonia': 'olive drab',
          'Japan': 'sea green'}


def draw_graph(nodes, edges, m, fname, type="со связями внутри"):
    G = nx.Graph()

    G.add_nodes_from(enumerate(nodes))

    if type == "без связей внутри":
        edges = [e for e in edges if G.node[e[0]]['country'] != G.node[e[1]]['country']]

    labels = []

    for i, d in enumerate(nodes):
        # G.node[i]['number'] = d['number']
        G.node[i]['title'] = d['title']
        G.node[i]['url'] = d['url']
        G.node[i]['country'] = d['country']
        G.node[i]['date'] = d['date']
        labels.append(G.node[i]['country'] + '<br>'
                      + G.node[i]['title'] + '<br>'
                      + G.node[i]['url'] + '<br>' +
                      G.node[i]['date']
                      )

    G.add_weighted_edges_from(edges)

    pos = nx.spring_layout(G)

    edge_trace = Scatter(
        x=[],
        y=[],
        text=list(G.edges(data='weight', default=0)),
        line=Line(width=0.5, color='#888'),
        hoverinfo='text',
        mode='lines')

    for edge in G.edges():
        edge_trace['x'] += [pos[edge[0]][0], pos[edge[1]][0], None]
        edge_trace['y'] += [pos[edge[0]][1], pos[edge[1]][1], None]

    node_trace = Scatter(
        x=[],
        y=[],
        text=labels,
        mode='markers',
        hoverinfo='text',
        hoveron='points+fills',
        marker=Marker(
            color=[],
            size=[],
            line=dict(width=1)))

    for nd in G.node.keys():
        node_trace['x'].append(pos[nd][0])
        node_trace['y'].append(pos[nd][1])

    for node, adjacencies in enumerate(G.adjacency()):
        node_trace['marker']['color'].append(COLORS[G.nodes[node]['country']])
        num_conn = len(adjacencies[1])
        if num_conn <= 6:
            node_trace['marker']['size'].append(6)
        elif num_conn >= 30:
            node_trace['marker']['size'].append(30)
        else:
            node_trace['marker']['size'].append(num_conn)

    fig = Figure(layout=Layout(
        title=fname + " " + datetime.today().strftime('%d/%m/%Y'),
        titlefont=dict(size=16),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[dict(
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002)],
        xaxis=XAxis(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=YAxis(showgrid=False, zeroline=False, showticklabels=False)),
        data=Data([edge_trace, node_trace]))

    py.plot(fig, filename=fname + str(m))


# for m in range(1, 5):
#     corp = Corpus()
#     data = Topnews(corp, mweight=m)
#
#     nodes = data.data
#     edges = data.edges
#     draw_graph(nodes, edges, m, fname="со связями внутри стран неделя")
#
# for m in range(1, 5):
#     corp = Corpus()
#     data = Topnews(corp, mweight=m)
#     nodes = data.data
#     edges = data.edges
#
#     draw_graph(nodes,edges,m,fname="без связей внутри стран неделя",type="без связей внутри")
