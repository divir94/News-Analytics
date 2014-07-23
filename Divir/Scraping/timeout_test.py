import time
import signal
from contextlib import contextmanager

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
        return "time out"

def foo(boo):
    #time.sleep(2)
    return boo

out = timeout(foo, 1, "hey")
print out
