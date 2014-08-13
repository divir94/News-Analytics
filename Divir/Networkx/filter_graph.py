import  networkx as nx

#G = read_gexf('../Data/Price-Heat-Graphs/2014-07-02.gexf')

def filter_price_change(G, threshold):
    for name in G:
        if G.node[name]['type'] == 'Company' and G.node[name]['price_change'] >= threshold: break

        neighbors = G.neighbors(name)
        significant = False

        for neighbor in neighbors:
            if G.node[name]['type'] == 'Company' and G.node[neighbor]['price_change'] >= threshold:
                significant = True
                break

        if not significant: G.remove_node(name)
        return G

G = nx.Graph()
G.add_node('a', type='Company', price_change=0.7)
G.add_node('b', type='Company', price_change=1.5)
G.add_node('c', type='Company', price_change=0)
G.add_node('d', type='Company', price_change=0.5)
G.add_node('e', type='Company', price_change=1.7)
G.add_node('f', type='Company', price_change=0.3)
G.add_edges_from([
    ('a','c'),
    ('a','d'),
    ('a','f'),
    ('b','e'),
    ('c','e'),
    ('c','f'),
    ('d','e')
])

#print G.nodes(data=True)
#print G.edges(data=True)

G = filter_price_change(G, 1)

print G.nodes(data=True)
print G.edges(data=True)
