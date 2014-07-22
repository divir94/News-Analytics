import networkx as nx
from pprint import pprint


G = nx.Graph()
G.add_node('1', label='A')
G.add_node('3', label='C')
G.add_node('2', label='B')
G.add_node('4', label='D')

G.add_edge(1, 3, spells=[('2014-07-01', '2014-07-02')], heat=[(2,'2014-07-01', '2014-07-02')])
G.add_edge(1, 2, spells=[('2014-07-01', '2014-07-02'), ('2014-07-03', '2014-07-04')], heat=[(1,'2014-07-01', '2014-07-02'), (4,'2014-07-03', '2014-07-04')])
G.add_edge(1, 4, spells=[('2014-07-02', '2014-07-03')], heat=[(3,'2014-07-02', '2014-07-03')])
G.add_edge(3, 2, spells=[('2014-07-03', '2014-07-04')], heat=[(1,'2014-07-03', '2014-07-04')])
G.add_edge(3, 4, spells=[('2014-07-01', '2014-07-02')], heat=[(5,'2014-07-01', '2014-07-02')])

nx.write_gexf(G, 'test2.gexf')

# G=nx.read_gexf('dynamics.gexf')
# pprint(G.nodes(data=True))
# pprint(G.edges(data=True))
