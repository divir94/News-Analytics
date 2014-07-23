from calais import Calais
from pprint import pprint
from random import choice
import networkx as nx
import shelve
import itertools

API_KEY = "kpfyb7kb5wqbhpxbdnxjr52v"
calais = Calais(API_KEY, submitter="python-calais demo")

def add_article_to_graph(G, article):
    # get content
    title, text = article
    content = "%s %s" % (title, text)
    content = content.encode('utf-8')

    # get entities
    entities = calais.analyze(content).entities

    # add to graph
    for entity in entities:
        name = entity["name"]
        if name not in G: G.add_node(entity["name"], type=entity["_type"])

    entity_names = [entities[i]["name"] for i in range(len(entities))]
    num_entities = len(entity_names)

    # add edge weights
    for i in range(num_entities):
        for j in range(i+1, num_entities):
            if G.has_edge(entity_names[i], entity_names[j]): G[entity_names[i]][entity_names[j]]["label"] += 1
            else: G.add_edge(entity_names[i], entity_names[j], label=1 )

d = shelve.open('20140701')
G = nx.Graph()

key = choice(d.keys())
print key
article = d[key]
add_article_to_graph(G, article)

pprint(G.nodes(data=True))
#pprint(G.edges(data=True))
#nx.write_gexf(G, 'test.gexf')

