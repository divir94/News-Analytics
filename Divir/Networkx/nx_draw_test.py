import matplotlib.pyplot as plt
import networkx as nx
from calais import Calais
import shelve
from time import *

API_KEY = "kpfyb7kb5wqbhpxbdnxjr52v"
calais = Calais(API_KEY, submitter="python-calais demo")

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
            time.sleep(120)
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


link ="http://www.reuters.com/article/2014/07/01/db-x-trackers-msci-world-idUSnBw015727a+100+BSW20140701"
articles_dict = shelve.open('../Data/July/2014-07-01', 'r')
title, text =  articles_dict[link]
#print title
#print text
content = "%s %s" % (title, text)
content = content.encode('utf-8')
#print content
entities = openCalis(content)
for entity in entities:
    print entity["name"]
articles_dict.close()


