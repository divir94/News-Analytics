# -*- coding: utf8 -*-
# entities
from calais import Calais

# netowrk
import networkx as nx
import matplotlib.pyplot as plt

# store
import shelve
import itertools

# time/ timeout
from contextlib import contextmanager
from datetime import date
import time
import signal

# other
from pprint import pprint
from random import choice




""" ----------------- Helper  ------------------"""
class TimeoutException(Exception): pass
def timeout(fun, limit, *args ):
    @contextmanager
    def time_limit(seconds):
        def signal_handler(signum, frame):
            raise TimeoutException, "Timed out!"
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try: yield
        finally: signal.alarm(0)
    try:
        with time_limit(limit):
            return fun(*args)
    except TimeoutException, msg:
        print "Function timed out\n"
        return None

def dict_slice(self, dict, begin, end):
          return dict(itertools.islice(dict.iteritems(), begin, end+1))


""" --------------- Entities Class ---------------"""

class EntitiesExtractor():
    def __init__(self, date, key_num=0, print_details=True):
        self.date = date
        self.date_str = str(date)
        self.path_to_articles = "../Data/Articles/"
        self.path_to_entities = "../Data/Entities/"
        self.API_KEYS = ["kpfyb7kb5wqbhpxbdnxjr52v", "6jzy64rda77s6un7vzw2rdu9", "vwk375uecnazrcrpu8n4y3yf"]
        self.calaisObj = Calais(self.API_KEYS[key_num], submitter="python-calais demo")
        self.print_details = print_details

    def get_entities(self, text):
        def clean(entity):
            del entity['_typeReference']
            del entity['instances']
            return entity
        response = "none"
        while response == "none":
            try:
                response = self.calaisObj.analyze(text)
            except ValueError:
                print "Calais Server Busy"
                time.sleep(120)
                response = "none"
        if response:
            try:
                return map(clean, response.entities)
            except:
                print "Calais failed!"
                print text
                return None
        else:
            return None

    def update_main_db(self, temp_dict):
        """
        :return: Update main db with temp dict to prevent corruption of db
        """
        main_db = shelve.open(self.path_to_entities + self.date_str, 'c')
        main_db.update(temp_dict)
        main_db.close()

    def log_link(self, link, status, title="", num_entities=-1):
        """
        :return: Store links in resp dict and print if asked
        """
        if self.print_details:
            if status=="entities-stored":
                print "%d: %s, %s, %d" % (self.counter, status, link, num_entities)
            else:
                print "%d: %s, %s, %s" % (self.counter, status, link, title)

    def run_read(self):
        entities_db = shelve.open(self.path_to_entities + self.date_str, 'r')
        counter = 0
        for link in entities_db:
            print "%d: %s %d entities" % (counter, link, len(entities_db[link]))
            counter += 1
        entities_db.close()


    def run_store(self):
        articles_db = shelve.open(self.path_to_articles + self.date_str, 'r')
        start_time = time.time()
        temp_dict = dict()

        self.counter = 0
        for link in articles_db:
            try:
                title, text = articles_db[link]
                if not title or not text:
                    self.log_link(link, "article-empty", title=title)
                    continue
                content = "%s %s" % (title, text)
                content = content.encode('utf-8')
            except:
                self.log_link(link, "article-key-corrupted", title="")
                continue

            entities = timeout(self.get_entities, 10, content)

            if entities:
                temp_dict[link] = entities
                self.log_link(link, "entities-stored", title, len(entities))
            else:
                self.log_link(link, "calais-failed", title)

            self.counter += 1
            if self.counter%20 == 0:
                self.update_main_db(temp_dict)
                if self.print_details: print "\nSuccessfully updated dict\n"
                temp_dict =dict()

        self.update_main_db(temp_dict)
        print "Time taken: %s sec" % str(time.time() - start_time)
        articles_db.close()


""" ------------- Main ---------------"""
my_date = date(2014, 7, 10)
extractor = EntitiesExtractor(my_date, 0)
extractor.run_read()

