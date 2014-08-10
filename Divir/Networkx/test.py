from matplotlib import pyplot as plt
import networkx as nx
G = nx.Graph()
G.add_edge(1,2)
G.add_edge(2,3)
for v in G.nodes():
    G.node[v]['state']='X'
G.node[1]['state']='Y'
G.node[2]['state']='Y'

for n in G.edges_iter():
    G.edge[n[0]][n[1]]['state']='X'
G.edge[2][3]['state']='Y'

pos = nx.spring_layout(G)

nx.draw(G, pos)
node_labels = nx.get_node_attributes(G,'state')
nx.draw_networkx_labels(G, pos, labels = node_labels)
edge_labels = nx.get_edge_attributes(G,'state')
nx.draw_networkx_edge_labels(G, pos, labels = edge_labels)
plt.savefig('heat-diffusion.png')
