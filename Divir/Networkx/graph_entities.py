# -*- coding: utf8 -*-
from pprint import pprint
from random import choice
from datetime import date
import time
import networkx as nx
import matplotlib.pyplot as plt
import shelve
import itertools

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
        self.path_to_graph = "../Data/Graphs/"

    def add_entities_to_graph(self, G, entities):
        entity_names = []
        # add nodes
        for entity in entities:
            try:
                name = entity['name']
                entity_names.append(name)
                if name in G:
                    G.node[name]['size'] += 1
                else:
                    G.add_node(name, type=entity['_type'], size=1)
            except: print "Failed to print name"

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

    def run_store(self):
        G = nx.Graph()
        start_time = time.time()
        counter = 0
        entities_db = shelve.open(self.path_to_entities + self.date_str, 'r')

        for link, entities in entities_db.iteritems():
            G = self.add_entities_to_graph(G, entities)
            print "%d: %s %d" % ( counter, link, len(G) )
            counter +=1

        entities_db.close()
        nx.write_gexf(G, self.path_to_graph + self.date_str + '.gexf')
        print "Time taken: %s sec" % str(time.time() - start_time)



""" ------------------- Main ------------------"""
for i in range(3,10):
    my_date = date(2014, 7, i)
    extractor = EntitiyGraph(my_date)
    extractor.run_store()
