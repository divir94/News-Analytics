import networkx as nx
from pprint import pprint

#G = nx.complete_graph(50)
#nx.write_gexf(G, 'test.gexf')

# G = nx.Graph()
# G.add_node('india', time='5pm')
# print G.nodes(data=True)

G=nx.read_gexf('../Gephi/dynamics.gexf')
pprint(G.nodes(data=True))
pprint(G.edges(data=True))
