# -*- coding: utf8 -*-
from pprint import pprint
from random import choice
from scipy.sparse.csgraph import laplacian
from scipy.linalg import expm
from datetime import date
import time
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import shelve
import itertools
import sys

""" ----------------- Helper  ------------------"""

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


""" ----------------- EntitiyGraph Class  ------------------"""

class EntitiyGraph():
    def __init__(self, date):
        self.date = date
        self.date_str = str(date)
        self.path_to_entities = "../Data/Entities/"
        self.path_to_graph = "../Data/Heat-Graphs/"

    def filter_node_type(self, type):
        noise = ['Anniversary', 'Date', 'EmailAddress', 'FaxNumber', 'PhoneNumber', 'URL', 'PersonEmailAddress']
        return type in noise

    def filter_node_size(self, G, threshold):
        for name in G.nodes():
            if G.node[name]['size'] < threshold:
                G.remove_node(name)
        return G

    def add_entities_to_graph(self, G, entities):
        entity_names = []
        # add nodes
        for entity in entities:
            if isinstance(entity, dict) and 'name' in entity:
                if self.filter_node_type(entity['_type']): continue
                name = entity['name']
                entity_names.append(name)
                if name in G:
                    G.node[name]['size'] += 1
                else:
                    G.add_node(name, type=entity['_type'], size=1)
            else:
                print "Failed to get entity name. %s" % type(entity)

        num_entities = len(entity_names)

        # add edge weights
        for i in range(num_entities):
            for j in range(i+1, num_entities):
                source, target = entity_names[i], entity_names[j]
                if G.has_edge(source, target):
                    G[source][target]['weight'] += 1
                else:
                    G.add_edge(source, target, weight=1 )
        return G

    def setEdgeWeights(self, G, adj_matrix, threshold):
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
                if G.has_edge(source, target):
                    weight = "%.3f" % adj_matrix.item((i, j))
                    if weight < threshold:
                        G.remove_edge(source, target)
                    else:
                        G.add_edge(source, target, weight=weight)
        return G

    def getHeatMatrix(self, G):
        print "adj matrix"
        start_time = time.time()
        A = nx.to_numpy_matrix(G)
        print time.time() - start_time

        print "laplacian"
        start_time = time.time()
        L = laplacian(A)
        print time.time() - start_time

        print "heat expm"
        start_time = time.time()
        heat_matrix = expm(-0.6*L)
        print time.time() - start_time

        return heat_matrix

    def run_store(self):
        G = nx.Graph()
        start_time = time.time()
        counter = 0
        entities_db = shelve.open(self.path_to_entities + self.date_str, 'r')

        for link, entities in entities_db.iteritems():
            G = self.add_entities_to_graph(G, entities)
            #print "%d: %s %d" % ( counter, link, len(G) )
            counter +=1

        entities_db.close()

        # filter nodes by size
        G = self.filter_node_size(G, 5)

        # heat diffusion matrix
        heat_matrix = self.getHeatMatrix(G)

        # make graph
        median = np.median(heat_matrix)
        H = self.setEdgeWeights(G, heat_matrix, 0)

        nx.write_gexf(G, self.path_to_graph + self.date_str + '.gexf')
        print "Time taken: %s sec" % str(time.time() - start_time)



""" ------------------- Main ------------------"""
for i in [2,3,4,6,7,8,9,10]:
    my_date = date(2014, 7, i)
    extractor = EntitiyGraph(my_date)
    extractor.run_store()
