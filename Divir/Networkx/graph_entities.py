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
import copy
import Quandl
import pandas as pd


""" ----------------- EntitiyGraph Class  ------------------"""

class EntitiyGraph():
    def __init__(self, date):
        self.date = date
        self.date_str = str(date)
        self.path_to_entities = "../Data/Entities/"
        self.path_to_graph = "../Data/Price-Heat-Graphs/"
        self.num_stock_prices = 0

    def filter_node_type(self, type):
        noise = ['Anniversary', 'Date', 'EmailAddress', 'FaxNumber', 'PhoneNumber', 'URL', 'PersonEmailAddress']
        return type in noise

    def filter_node_size(self, G, threshold):
        for name in G.nodes():
            if G.node[name]['size'] < threshold:
                G.remove_node(name)
        return G

    def get_stock_price(self, entity, ticker_db):
        # check if ticker in entity
        if 'resolutions' in entity and 'ticker' in entity['resolutions'][0]:
            ticker = str(entity['resolutions'][0]['ticker'])

            if ticker in ticker_db:
                data = ticker_db[ticker]
                if data.empty:
                    print "Found in db - Ticker: %s, Empty" % (ticker)
                    return [ticker]+[0]*3

                try:
                    open = data['Open'][self.date_str]
                    close = data['Close'][self.date_str]
                    price_change = float('%.2f' % ( (close-open)*100 / float(open) ))

                    self.num_stock_prices += 1
                    print "Found in db - Ticker: %s, Price change: %.2f" % (ticker, price_change)
                    return ticker, open, close, price_change
                except:
                    print "Found in db - Ticker: %s, Date not found" % (ticker)
                    return [ticker]+[0]*3


            # get price change
            try:
                code = ''

                # find code for a dataset with 1) stock prices 2) daily frequency
                datasets = datasets = Quandl.search(ticker +' stock price', verbose = False)
                for dataset in datasets:
                    if  dataset['freq']=='daily' and 'Open' in dataset['colname']:
                        code = dataset['code']
                        break
                print ticker, code
                if code == '': code = 'GOOG/NASDAQ_'+ticker

                # get stock prices
                data = Quandl.get(code, trim_start=self.date_str, trim_end=self.date_str, collapse="daily", authtoken="EqhJyL2Ywt3Q-hxydsN3")
                 # log
                self.num_stock_prices += 1
                ticker_db[ticker] = data

                open = data['Open'][self.date_str]
                close = data['Close'][self.date_str]
                price_change = float('%.2f' % ( (close-open)*100 / float(open) ))
                print "Ticker: %s, Price change: %.2f" % (ticker, price_change)
                return ticker, open, close, price_change

            except:
                ticker_db[ticker] = pd.DataFrame()
                print "Exception: Ticker: %s, Price change not found" % (ticker)
                return [ticker]+[0]*3
        else:
            return ['']+[0]*3


    def add_entities_to_graph(self, G, entities):
        entity_names = []
        # add nodes
        for entity in entities:
            if isinstance(entity, dict) and 'name' in entity:
                name = entity['name']
                type = entity['_type']
                # filter node types
                if self.filter_node_type(type): continue
                entity_names.append(name)
                # add/update node
                if name in G:
                    G.node[name]['size'] += 1
                else:
                    G.add_node(name, type=type, size=1, entity=entity)
            else:
                print "Failed to get entity name"

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
        print "Graph size before filtering by node size: %d" % len(G)
        G = self.filter_node_size(G, 2)
        print "Graph size after filtering by node size: %d" % len(G)

        ticker_db = shelve.open(self.path_to_graph + 'ticker')
        i = 0
        for name in G:
            if G.node[name]['type'] == 'Company':
                entity = G.node[name]['entity']
                ticker, open, close, price_change = self.get_stock_price(entity, ticker_db)

                G.node[name]['ticker'] = ticker
                G.node[name]['open'] = float(open)
                G.node[name]['close'] = float(close)
                G.node[name]['price_change'] = float(price_change)

                if i%20 == 0:
                    ticker_db.close()
                    ticker_db = shelve.open(self.path_to_graph + 'ticker')
                    print "%d: Saved tickers to db" % i
                i += 1
        ticker_db.close()

        # heat diffusion matrix
        heat_matrix = self.getHeatMatrix(G)

        # make graph
        #median = np.median(heat_matrix)
        H = self.setEdgeWeights(G, heat_matrix, 0)
        print "Num stock prices: %d\n" % self.num_stock_prices

        nx.write_gexf(G, self.path_to_graph + self.date_str + '.gexf')
        print "Time taken: %s sec" % str(time.time() - start_time)



""" ------------------- Main ------------------"""
for i in [7, 8, 9, 10]:
    my_date = date(2014, 7, i)
    extractor = EntitiyGraph(my_date)
    extractor.run_store()
