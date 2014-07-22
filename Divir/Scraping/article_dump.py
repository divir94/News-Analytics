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


"""
key: date (yy/mm/dd) i.e. 20070701
value: list of tuples where every tuple is (title, meta, text) i.e. [(title, meta, text), (...), (...)]
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
     
""" ------------- Special Functions ---------------"""
def article_links_on_date(date):
     url = "http://www.reuters.com/resources/archive/us/%s.html" % date
     html = get_html(url)
     article_links = find_tags(html, 'div', 'headlineMed', a_tag=True)
     return article_links

def store_articles(date, limit=float("Inf")):
     d = shelve.open(date, writeback=True)
     article_links = article_links_on_date(date)
     num_articles = min(limit, len(article_links))
     #print len(article_links)

     # get and store articles for all links
     for i in range(num_articles):
        link = str(article_links[i])
        # get article and write to dict
        if link not in d and "video" not in link: d[link] = get_article(link)
        if d[link][0] == ("", ""): print link
        # sync after every 16 articles
        if i%16==0: d.sync()
     d.close()
     return

def print_article_titles(date):
     d = shelve.open(date)
     for url, article in d.iteritems():
        print url, article[0]

def get_range(dictionary, begin, end):
  return dict(itertools.islice(dictionary.iteritems(), begin, end+1))


# date = "20140710"
# start_time = time()
# store_articles(date)
# print time() - start_time

print_article_titles('20140710')
#d = shelve.open("20140710")