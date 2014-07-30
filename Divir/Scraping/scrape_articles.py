# -*- coding: utf8 -*-
# scraping
import urllib2
from goose import Goose
from bs4 import BeautifulSoup

# db
import shelve

# time/timeout
import signal
from datetime import *
from contextlib import contextmanager
from time import time

# others
import itertools
import sys
from pprint import pprint
from collections import OrderedDict


"""
articles_dict
key: date (yymmdd) i.e. 20070701
value: dict with key: val -> url: (title, text)
"""

""" ------------- Generic Scraping ---------------"""

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


""" ----------------- Helper  ------------------"""

def dates_in_interval(start_date, end_date):
    """ Returns list of calender dates in interval"""
    diff = end_date - start_date
    dates = [ start_date + timedelta(i) for i in range(diff.days + 1) ]
    return dates

# for date in dates_in_range(date(2014,6,15), date(2014,7,15)): print date


def store_num_articles(start_date, end_date):
    dates = dates_in_range(start_date, end_date)
    num_dates = len(dates)
    total_articles = 0
    temp_dict = dict()

    # 1
    main_dict = shelve.open("../Data/num_articles")
    dates_stored = [date for date in main_dict]
    main_dict.close()

    for i in range(num_dates):
        date = str(dates[i])
        if date in dates_stored:
            print "Date: %s in dict" % date
            continue

        try:
            articles_list = timeout(article_links_on_date, 5, date)
            if isinstance(articles_list, list):
                num_articles = len(articles_list)
                total_articles += num_articles
                temp_dict[str(date)] = num_articles
                print "Date: %s, Num articles: %s" % ( date, num_articles )
        except: "\nFailed to get articles list on date %s\n" % date

        # write to dict
        if i%20 == 0:
            main_dict = shelve.open("../Data/num_articles")
            main_dict.update(temp_dict)
            main_dict.close()
            temp_dict = dict()
            print "\nSuccessfully updated dict, date: %s\n" % ( date )

    print "\nTotal articles: %s" % total_articles

def print_num_articles():
    d = shelve.open("../Data/num_articles")
    total_articles = 0
    missing_dates = []
    calender_dates = dates_in_range( date(2007,1,1), date(2014,7,26) )
    ordered_dict = OrderedDict((datetime.strftime(datetime.strptime(k , '%Y-%m-%d'), '%Y-%m-%d'), v)
                           for k, v in sorted(d.iteritems()))

    # print ordered dates in dict
    for my_date, num_articles in ordered_dict.items():
        total_articles += num_articles
        print "Date: %s, Num articles: %s" % ( my_date, num_articles )

    print "\nNum dates on calender: %d" % len(calender_dates)
    print "Num dates stored: %d" % len(ordered_dict)
    print "Total articles: %d" % total_articles

    # print and get missing dates
    print "\nMissing dates:"
    for my_date in calender_dates:
        if str(my_date) not in d:
            print my_date
            d[str(my_date)] = len(article_links_on_date(my_date))
    d.close()

# print_num_articles()

""" --------------- Scraper Class ---------------"""

class ArticleScraper():
    def __init__(self, date, print_details=True):
        self.date = date
        self.date_str = str(date)
        self.path_to_data = "../Data/July/"
        self.reuters_article_links = [] # total articles on reuters
        self.corrupted_keys = [] # failed to read key from db
        self.pre_stored_links = [] # already stored in db and title not empty
        self.stored_links = [] # stored in current process
        self.crashed_links = [] # DB or Goose crashed while extracting
        self.empty_links = [] # Goose returned w/ empty title
        self.empty_db_links = []
        self.print_details = print_details

    def get_article_links(self):
        """
        :return: List of article urls for a given date
        """
        reuters_date_format = self.date_str.replace("-","")
        url = "http://www.reuters.com/resources/archive/us/%s.html" % reuters_date_format
        html = get_html(url)
        # all links includes articles + video
        all_links = find_tags(html, 'div', 'headlineMed', a_tag=True)
        # remove video links
        self.reuters_article_links = [link for link in all_links if 'video' not in str(link)]
        return self.reuters_article_links

    def get_pre_stored_links(self, details=False):
        """
        :return: List of stored articles for a given date
        """
        main_db = shelve.open(self.path_to_data + self.date_str, "r")
        for link in main_db:
            try:
                title, text = main_db[link]
                if title: self.log_link(link, "prestored-log", title, details)
                if title =="" or text == "" or title == None or text == None:
                    self.log_link(link, "empty-db", title)
            except:
                self.log_link(link, "corrupted-key")
        main_db.close()
        return self.pre_stored_links


    def store_article(self, link, temp_dict):
        """
        :param temp_dict: temp dict to update main db
        :return: Store and log article
        """
        try: title, text = timeout(get_article, 5, link)
        except:
            self.log_link(link, "crashed")
            return
        if title:
            temp_dict[link] = ( title, text )
            self.log_link(link, "stored", title)
        else: self.log_link(link, "empty")


    def log_link(self, link, status, title="", details=True):
        """
        :return: Store links in resp dict and print if asked
        """
        if self.print_details and details: print "Status: %s, %s, %s" % (status, link, title)
        if status == "crashed":
            self.crashed_links.append(link)
        elif status == "empty":
            self.empty_links.append(link)
        elif status == "stored":
            self.stored_links.append(link)
        elif status == "prestored-log":
            self.pre_stored_links.append(link)
        elif status == "pprestored-nolog": pass
        elif status == "corrupted-key":
            self.corrupted_key.append(link)
        elif status == "empty-db":
            self.empty_db_links.append(link)


    def update_main_db(self, temp_dict):
        """
        :return: Update main db with temp dict to prevent corruption of db
        """
        main_dict = shelve.open(self.path_to_data + self.date_str, "wb")
        main_dict.update(temp_dict)
        main_dict.close()


    def print_read_results(self):
        """
        :return: Print results after reading db
        """
        if self.print_details:
            print "\n\nCorrupted keys:"
            for link in self.corrupted_keys: print link

            print "\n\nEmpty db links:"
            for link in self.empty_db_links: print link

        print "\nReuter's: %d" % len(self.get_article_links())
        print "Pre-stored: %d" % len(self.pre_stored_links)
        print "Empty: %d" % len(self.empty_db_links)
        print "Corrupted keys: %d" % len(self.corrupted_keys)


    def print_store_results(self):
        """
        :return: Print results after updating db
        """
        if self.print_details:
            print "\nEmpty articles:"
            for link in self.empty_links: print link
            print "\nCrashed articles:"
            for link in self.crashed_links: print link

        print "\nReuter's: %d" % len(self.reuters_article_links)
        print "Stored: %d" % len(self.stored_links)
        print "Crashed: %d" % len(self.crashed_links)
        print "Empty: %d" % len(self.empty_links)


    def test_link(self, link):
        title, text = get_article(link)
        print title
        print text

    def run_read(self):
        """
        :return: Print articles in db
        """
        print "\n\nDate: %s" % self.date_str
        self.get_pre_stored_links(details=True)
        self.print_read_results()

    def run_store(self):
        """
        :return: Update main db with temp dict to prevent corruption of db
        """
        print "Date: %s" % self.date_str
        start_time = time()
        temp_dict = dict()
        article_links = self.get_article_links()
        num_articles = len(article_links)
        pre_stored_articles = self.get_pre_stored_links()

        # store, log and update main db
        for i in range(num_articles):
            link = article_links[i]
            # check if already stored
            if link in pre_stored_articles:
                self.log_link(link, "prestored-nolog")
                continue
            # store and log
            self.store_article(link, temp_dict)
            # open and update main db, clear temp dict
            if i%20 == 0:
                self.update_main_db(temp_dict)
                if self.print_details: print "\nSuccessfully updated dict, i: %d, num links: %d\n" % ( i, num_articles)

        # print results
        self.print_store_results()
        print "Time taken: %s sec" % str(time() - start_time)



""" ------------- Main ---------------"""

for i in range(1,11):
    my_date = date(2014,7,i)
    scraper = ArticleScraper(my_date, False)
    scraper.run_read()