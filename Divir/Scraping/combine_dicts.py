import shelve

dates = range(1, 11)
dates = ['2014070%s'%date for date in dates] 
d = shelve.open('../Data/July/July')

def combine(d):
     for date in dates:
          temp = shelve.open('July/%s'%date)
          d[date] = dict(temp)
     d.sync()
     
def print_keys(d):
     for key, val in d.iteritems():
          print key, len(val)

#combine(d)
print_keys(d)
d.close()    

