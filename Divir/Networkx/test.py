import datetime as dt
import sys
import Quandl

def getValueChange(self, ticker, start, end):
    import Quandl
    from dateutil.relativedelta import relativedelta
    stockPriceResponse = self.pastPrices.get(ticker, "fetch")
    if stockPriceResponse=="fetch":
        try:
            #mrktCapResponse = Quandl.get("DMDRN/"+ticker+"_MKT_CAP", trim_start=str(start), trim_end=str(end), collapse="annual", authtoken="xaYsva9sQfpTwzq7NVoz")
            stockPriceResponse =  Quandl.get("GOOG/NASDAQ_"+ticker, trim_start=str(start), trim_end=str(end), collapse="daily", authtoken="xaYsva9sQfpTwzq7NVoz")

        except:
            print "failed on "+ticker+" from ",start, " to ", end
            return 0
    #assert len(mrktCapResponse.index)==1
    #mrktCap = mrktCapResponse[mrktCapResponse.keys()[0]][mrktCapResponse.index[0]]
    while str(start) not in stockPriceResponse.Close:
        start = start + relativedelta(days=1)
        print "new start date ", start
    while str(end) not in stockPriceResponse.Close:
        end = end - relativedelta(days=1)
        print "new end date ", end
    startPrice = stockPriceResponse["Close"][str(start)]
    endPrice = stockPriceResponse["Close"][str(end)]
    return abs((endPrice-startPrice)/startPrice)>0.01
#Example Usage:
# print getPriceChange(AAPL, dt.date(2013, 1, 4), dt.date(2013, 2, 4))


date = '2014-08-08'
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
        print data['Open']
        print data['Open']['2001-07-05']
        # open = data['Open'][date]
        # close = data['Close'][date]
        # price_change = float('%.2f' % ( (close-open)*100 / float(open) ))
        # print "Ticker: %s, Price change: %f" % (ticker, price_change)
        # return ticker, open, close, price_change
    except:
        print "Exception: Ticker: %s, Price change not found" % (ticker)
        return [ticker]+[0]*3

#get_stock_price('AAPL')
