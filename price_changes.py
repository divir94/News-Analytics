import pandas.io.data as web
from datetime import datetime

# Ticker and time interval
ticker = "IBM"
source = 'yahoo'
start = datetime(2014, 6, 1)
end = datetime(2014, 6, 13)

# Start and end price
price_change=web.DataReader(ticker, source, start, end)
print price_change
print "Opening price for interval: %s \nClosing price for interval: %s" % (price_change["Open"][0], price_change["Open"][-1])
