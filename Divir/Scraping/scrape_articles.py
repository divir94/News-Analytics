# -*- coding: utf8 -*-
# scraping
import urllib2
from goose import Goose
from bs4 import BeautifulSoup

# db
import shelve

# others
import itertools
import sys
from pprint import pprint
from time import time

# timeout
import signal
from contextlib import contextmanager



"""
key: date (yy/mm/dd) i.e. 20070701
value: list of dicts where key is url and value is (title, text) i.e. url: (title, text)
"""


""" ------------- Generic Functions ---------------"""
# html
def get_html(url):
   """"given a url return html"""
   try:
       html = urllib2.urlopen(url).read()
       return html
   except urllib2.HTTPError, e:
       print "URL broke: %s" % url
       return None

# tags
def find_tags(html, tag_name, class_name=False, a_tag=False):
   """"find tags using beutifulsoup,
       options: use class names, get anchor tags"""
   soup = BeautifulSoup(html)
   # get tag with class if specified
   if class_name: tags = soup.findAll(tag_name, { "class" : class_name })
   else: tags = soup.findAll(tag_name)
   # get anchor tag if specified
   if a_tag: tags = [link.find("a")["href"] for link in tags]
   return tags

# article
def get_article(url):
     """get article title, meta data and text using goose"""
     g = Goose()
     article = g.extract(url=url)
     title = article.title
     text = article.cleaned_text
     return (title, text)

class TimeoutException(Exception): pass
def timeout(fun, limit, *args ):
    @contextmanager
    def time_limit(seconds):
        def signal_handler(signum, frame):
            raise TimeoutException, "Timed out!"
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
    try:
        with time_limit(limit):
            return fun(*args)
    except TimeoutException, msg:
        return ("", "")

""" ------------- Special Functions ---------------"""
def article_links_on_date(date):
     url = "http://www.reuters.com/resources/archive/us/%s.html" % date
     html = get_html(url)

     # all links includes articles + video
     all_links = find_tags(html, 'div', 'headlineMed', a_tag=True)
     article_links = [i for i in all_links if 'video' not in str(i)]
     return article_links

def store_articles(date):
     d = shelve.open("../Data/July/" + date, writeback=True)
     num_stored = num_missing = 0

     # get links to articles
     article_links = article_links_on_date(date)

     # store articles
     for link in article_links:
        if link not in d or not d[link][0] or not d[link][1]:
            try:
                d[link] = timeout(get_article, int(5), link)
                print link, d[link][0]
            except: pass
            #d[link] = get_article(link)
            num_missing += 1
        else:
            num_stored += 1

     print "Stored: %d" % num_stored
     print "Missing: %d" % num_missing
     d.close()
     return

def print_article_titles(date):
     d = shelve.open("../Data/July/" + date)
     empty_articles  = 0
     for url, (title, text) in d.iteritems():
        print url, title
        if not title or not text: empty_articles +=1
     print "\nNum articles on Reuters: %d" % len(article_links_on_date(date))
     print "Num articles in dict: %d" % len(d)
     print "Empty articles in dict: %d" % empty_articles


def run_store(date):
    start_time = time()
    store_articles(date)
    print time() - start_time


date = "20140702"

print_article_titles(date)
#run_store(date)

# d = shelve.open("../Data/July/" + date)
# print len(d)
