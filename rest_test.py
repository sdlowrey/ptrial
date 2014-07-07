# From Python Cookbook, 3rd ed.
# modifications for time series use

import json
import observer
import Queue
from threading import Thread
import time

_hello_resp = '''\
<html>
  <head>
     <title>Hello {name}</title>
   </head>
   <body>
     <h1>Hello {name}!</h1>
   </body>
</html>'''

def hello_world(environ, start_response):
    start_response('200 OK', [ ('Content-type','text/html')])
    params = environ['params']
    resp = _hello_resp.format(name=params.get('name'))
    yield resp.encode('utf-8')

_localtime_resp = '''\
<?xml version="1.0"?>
<time>
  <year>{t.tm_year}</year>
  <month>{t.tm_mon}</month>
  <day>{t.tm_mday}</day>
  <hour>{t.tm_hour}</hour>
  <minute>{t.tm_min}</minute>
  <second>{t.tm_sec}</second>
</time>'''

def localtime(environ, start_response):
    start_response('200 OK', [ ('Content-type', 'application/xml') ])
    resp = _localtime_resp.format(t=time.localtime())
    yield resp.encode('utf-8')

def diskstats(environ, start_response):
    global q
    start_response('200 OK', [ ('Content-type', 'application/json') ])
    params = environ['params']
    part = params.get('part')
    end = object()  #stupid hack
    out = []
    while True:
        try:
            data = q.get(block=False)
            print "got data"
        except Queue.Empty:
            print "queue is empty"
            break
        out.append(data)
        q.task_done()
            
    resp = json.dumps(out)
    yield resp.encode('utf-8')
    
def ctrl(environ, start_response):
    global run
    start_response('200 OK', [ ('Content-type', 'application/json') ])
    params = environ['params']
    cmd = params.get('cmd')
    resp = 'unknown command'
    if cmd == 'shutdown':
        run = False
        resp = 'stopping'
    yield resp.encode('utf-8')
        
if __name__ == '__main__':
    from resty import PathDispatcher
    from wsgiref.simple_server import make_server

    # Create the dispatcher and register functions
    dispatcher = PathDispatcher()
    dispatcher.register('GET', '/hello', hello_world)
    dispatcher.register('GET', '/localtime', localtime)
    dispatcher.register('GET', '/diskstats', diskstats)
    dispatcher.register('GET', '/ctrl', ctrl)
    
    # spin up the Observer thread for disk stats
    obs = observer.StorageObserver('var partition', data_format=observer.JSON_DATA)
    obs.set_device('/var')
    global q
    q = Queue.Queue()
    t = Thread(target=obs.run, kwargs={'outq': q})
    t.start()
    time.sleep(5) # get some data in the queue
    
    # Launch a basic server
    global run
    run = True
    httpd = make_server('', 8080, dispatcher)
    print('Serving on port 8080...')
    while run:
        httpd.handle_request()
    # throw out the rest of the items in the queue and stop the observer thread
    obs.stop()
    tossed = 0
    while not q.empty():
        tossed += 1
        q.get()
        q.task_done()
    print 'tossed {} queue items'.format(tossed)
    q.join()
    print 'shutdown complete'