import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from scipy import linalg

def createGraph():
    G = nx.Graph()
    G.add_nodes_from([
        ('A', {'size': 2, 'type': 'Company'}),
        ('B', {'size': 1, 'type': 'Person'}),
        ('C', {'size': 5, 'type': 'City'})
    ])

    G.add_weighted_edges_from([
        ('A','B', 1),
        ('A','C', 2),
        ('B','C', 3)
    ])
    return G

def setEdgeWeights(G, adj_matrix, threshold):
    '''
    :param G: networkx undirected graph
    :param adj_matrix: numpy adj matrix with order G.nodes()
    :return: G with edge weights from adj_matrix
    '''
    size = len(G)
    nodes = G.nodes()
    for i in range(1, size):
        for j in range(i):
            source, target = nodes[i], nodes[j]
            weight = "%.3f" % adj_matrix.item((i, j))
            if weight < threshold:
                G.remove_edge(source, target)
            else:
                G[source][target]['weight'] = weight
    return G

def getHeatMatrix(G):
    L = nx.laplacian_matrix(G)
    L = L.todense()
    heat_matrix = linalg.expm(-L)
    return heat_matrix

def drawGraph(G):
    pos = nx.spring_layout(G)
    # nodes
    nx.draw_networkx_nodes(G,pos,node_size=600, node_color="white")
    # edges
    nx.draw_networkx_edges(G,pos, width=6,alpha=0.5,edge_color='black')
    # labels
    nx.draw_networkx_labels(G,pos,font_size=20,font_family='sans-serif')
    nx.draw_networkx_edge_labels(G, pos,  label_pos=0.3)
    # axis and save
    plt.axis('off')
    plt.savefig('heat-diffusion-2.png')


G = createGraph()
heat_matrix = getHeatMatrix(G)
H = setEdgeWeights(G, heat_matrix, 0)
print H.edge['A']['B']









