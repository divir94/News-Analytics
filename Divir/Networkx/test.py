import datetime as dt
import sys
import Quandl

def get_stock_price(ticker):
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
        data = Quandl.get(code, collapse="daily", authtoken="EqhJyL2Ywt3Q-hxydsN3")
        open = data['Open'][date]
        close = data['Close'][date]
        price_change = float('%.2f' % ( (close-open)*100 / float(open) ))
        print "Ticker: %s, Price change: %.2f" % (ticker, price_change)
        return ticker, open, close, price_change
    except:
        print "Exception: Ticker: %s, Price change not found" % (ticker)
        return [ticker]+[0]*3

date = '2014-07-01'
get_stock_price('FB')
