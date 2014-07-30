import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from itertools import combinations

def merge_graph(G, H):
    '''
    :param G: Graph to add nodes and edges to
    :param H: Graph to add nodes and edges from
    :return: merged graph G
    '''
    nodeList = H.nodes(data=True)
    edgeList = H.edges(data=True)

    # add nodes from H to G
    for node in nodeList:
        if not G.has_node(node): G.add_nodes_from([node])

    # add edges from H to G
    for edge in edgeList:
        source, target, weight =  edge
        if G.has_edge(source, target):
            G[source][target]['weight'] += H[source][target]['weight']
        else: G.add_edges_from([edge])

    return G

def complete_graph_from_list(nodeList):
    '''
    :param nodeList: list of nodes e.g. ["b", "d", "e"] or [("b", {'type': 'stock'}), ("c", {'type': 'food'})]
    :return: complete graph with edge weight = 1
    '''
    # check if nodeList has data
    if (isinstance(nodeList[0], tuple)): nodeList, data = [list(t) for t in zip(*nodeList)]
    edgeList = combinations(nodeList, 2)
    G = nx.Graph()

    # add nodes and edge
    for node in nodeList: G.add_node(node)
    G.add_edges_from(edgeList, weight=1)
    return G


# testing

# G = complete_graph_from_list(["a", "b", "c", "d"])
# H = complete_graph_from_list(["b", "d", "e"])
#
# C = merge_graph(G, H)
# pprint(C.nodes())
# pprint(C.edges(data=True))
#
# nx.draw_spring(G)
# plt.show()

# A = nx.adjacency_matrix(C, ["a", "b", "c", "d", "e"])
# pprint(A.toarray())

nodeList = [("b", {'type': 'stock'}), ("c", {'type': 'food'})]
G = complete_graph_from_list(nodeList)
pprint(G.nodes(data=True))