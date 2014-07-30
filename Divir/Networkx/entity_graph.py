# -*- coding: utf8 -*-
from calais import Calais
from pprint import pprint
from random import choice
from time import *
import networkx as nx
import matplotlib.pyplot as plt
import shelve
import itertools

API_KEY = "kpfyb7kb5wqbhpxbdnxjr52v"
#API_KEY = "vwk375uecnazrcrpu8n4y3yf"
calais = Calais(API_KEY, submitter="python-calais demo")

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

def openCalis(text):
    def clean(entity):
        del entity['_typeReference']
        del entity['instances']
        return entity
    response = "none"
    while response == "none":
        try:
            response = calais.analyze(text)
        except ValueError:
            print "Calais Server Busy"
            sleep(120)
            response = "none"
    if response:
        try:
            return map(clean, response.entities)
        except:
            print "calis failed!"
            print text
            return None
    else:
        return None

def add_article_to_graph(G, article):
    # get content
    title, text = article
    content = "%s %s" % (title, text)
    content = content.encode('utf-8')

    # get entities
    entities = openCalis(content)

    # add nodes to graph
    for entity in entities:
        name = entity["name"]
        if name not in G: G.add_node(entity["name"], type=entity["_type"])

    entity_names = [entities[i]["name"] for i in range(len(entities))]
    num_entities = len(entity_names)

    # add edge weights
    for i in range(num_entities):
        for j in range(i+1, num_entities):
            #if G.has_edge(entity_names[i], entity_names[j]): G[entity_names[i]][entity_names[j]]["weight"] += 1
            G.add_edge(entity_names[i], entity_names[j], weight=1 )
    return G

import itertools
def get_range(dictionary, begin, end):
  return dict(itertools.islice(dictionary.iteritems(), begin, end+1))

# date = '2014-07-02'
# articles_dict = shelve.open('../Data/July/'+date, 'r')
# entities_dict = shelve.open('../Data/Entities/'+date)
# start_time = time()
# #sub_articles = get_range(articles_dict, 0, 20)
# #articles_dict.close()
#
# counter = 0
# for link, article in articles_dict.items():
#     G = nx.Graph()
#     try:
#         if link not in entities_dict or entities_dict[link]==None or len(entities_dict[link])==0:
#             G = add_article_to_graph(nx.Graph(), article)
#             entities_dict[link] = G
#             sleep(2)
#     except:
#         print "Calais crashed on link: %s" % link
#         continue
#     print "%d: %s %d" % (counter, link, len(entities_dict[link]))
#     counter += 1
#
# print "Time taken: %s sec" % str(time() - start_time)
# entities_dict.close()
# articles_dict.close()



start_time = time()
entities_dict = shelve.open('../Data/Entities/2014-07-01', 'r')
print len(entities_dict)
G = nx.Graph()
counter = 0
for link in entities_dict:
    try:
        print "%d: %s %d" % ( counter, link, len(entities_dict[link]) )
        merge_graph(G, entities_dict[link])
        counter +=1
    except:
        print "Link broken: %s" % ( link )
print "Time taken to merge: %s sec" % str(time() - start_time)
entities_dict.close()

for edge in G.edges(data=True):
    source, target, data = edge
    weight = data['weight']
    #if weight>1: print "Source: %s, Target: %s, Weight: %s" % (source, target, data)

print len(G)
# nx.draw_spring(G)
# plt.savefig("graph.pdf")
#plt.show()

nx.write_gexf(G, 'graph.gexf')




