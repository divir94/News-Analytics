# -*- coding: utf8 -*-
# scraping
import urllib2
from goose import Goose
from bs4 import BeautifulSoup

# db
import shelve

# time/timeout
import signal
from datetime import date, timedelta
from contextlib import contextmanager
from time import time

# others
import itertools
import sys
from pprint import pprint


"""
articles_dict
key: date (yymmdd) i.e. 20070701
value: dict with key: val -> url: (title, text)
"""


""" ------------- Generic Functions ---------------"""
# html
def get_html(url):
   """"given a url returns html"""
   try:
       html = urllib2.urlopen(url).read()
       return html
   except urllib2.HTTPError, e:
       print "URL broke: %s" % url
       return None

# tags
def find_tags(html, tag_name, class_name=False, a_tag=False):
   """"find tags using beautifulsoup,
       options: use a class name, get anchor tags"""
   soup = BeautifulSoup(html)
   # get tag with class if specified
   if class_name: tags = soup.findAll(tag_name, { "class" : class_name })
   else: tags = soup.findAll(tag_name)
   # get anchor tag if specified
   if a_tag: tags = [link.find("a")["href"] for link in tags]
   return tags

# article
def get_article(url):
     """get article title and text using goose"""
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
        try: yield
        finally: signal.alarm(0)
    try:
        with time_limit(limit):
            return fun(*args)
    except TimeoutException, msg:
        print "Function timed out\n"
        return ("", "")

""" ------------- Scrape Articles ---------------"""
def article_links_on_date(date):
     reuters_date_format = str(date).replace("-","")
     url = "http://www.reuters.com/resources/archive/us/%s.html" % reuters_date_format
     html = get_html(url)
     # all links includes articles + video
     all_links = find_tags(html, 'div', 'headlineMed', a_tag=True)
     # remove video links
     article_links = [link for link in all_links if 'video' not in str(link)]
     return article_links

def dates_in_range(start_date, end_date):
    diff = end_date - start_date
    dates = [ start_date + timedelta(i) for i in range(diff.days + 1) ]
    return dates
# test
# for date in dates_in_range(date(2014,6,15), date(2014,7,15)): print date

def print_articles_on_dates(start_date, end_date):
    dates = dates_in_range(start_date, end_date)
    total_articles = 0
    for date in dates:
        num_articles = len(article_links_on_date(date))
        total_articles += num_articles
        print "Date: %s, Num articles: %s" % ( str(date), num_articles )
    print "\nTotal articles: %s" % total_articles
# test
# print_articles_on_dates(date(2014,7,1), date(2014,7,10))

""" ------------- Store Articles ---------------"""
def run_store(date):
    start_time = time()
    store_articles(date)
    print time() - start_time

def store_articles(date):
     d = shelve.open("../Data/July/" + str(date), writeback=True)
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

""" ------------- Printing ---------------"""

def print_article_titles(date):
     d = shelve.open("../Data/July/" + str(date))
     empty_articles  = 0
     for url, (title, text) in d.iteritems():
        print url, title
        if not title or not text: empty_articles +=1
     print "\nNum articles on Reuters: %d" % len(article_links_on_date(date))
     print "Num articles in dict: %d" % len(d)
     print "Empty articles in dict: %d" % empty_articles


date = date(2014,7,1)

# print_article_titles(date)
# run_store(date)

# d = shelve.open("../Data/July/" + str(date))
# print len(d)

