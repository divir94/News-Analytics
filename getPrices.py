'''
Created on Jun 2, 2014

@author: vidurjoshi
'''


from pandas.io import parsers
from datetime import datetime



def make_url(ticker_symbol,start_date, end_date):
    print ticker_symbol
    base_url = "http://ichart.finance.yahoo.com/table.csv?s="
    a = start_date
    b = end_date
    dt_url = '%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=d&ignore=.csv'% (ticker_symbol, a.month-1, a.day, a.year, b.month-1, b.day,b.year)
    return base_url + dt_url


def getPrices(symb, openD, closeD):
    url = make_url(symb,openD, closeD)
    print url
    e = parsers.read_csv(url)
    print e

getPrices("GOOG", datetime(2000,1,1), datetime(2012,1,1))