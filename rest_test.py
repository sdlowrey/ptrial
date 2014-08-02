
import json
from ptrial.observer.core import JSON_DATA, CSV_DATA
from ptrial.observer.kernel import StorageObserver
from Queue import Queue
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
    """
    Generate a response using all data in the queue.
    """
    # hardcoded to CSV delimited by newline with headers on first line
    # TODO: JSON should create a single object with all queue items as records?
    global obs, q
    start_response('200 OK', [ ('Content-type', 'text/csv') ])
    params = environ['params']
    part = params.get('part')  # not sure what this is...
    yield obs.field_names + '\n'
    while True:
        try:
            data = q.get(block=False)
            yield data.encode('utf-8') + '\n'
            q.task_done()
        except Queue.Empty:
            print "queue is empty"
            break
    
def ctrl(environ, start_response):
    global run
    start_response('200 OK', [ ('Content-type', 'text/plain') ])
    params = environ['params']
    cmd = params.get('cmd')
    resp = 'unknown command'
    if cmd == 'shutdown':
        run = False
        resp = 'stopping'
    elif cmd == 'status':
        resp = json.dumps(obs.status())
    yield resp.encode('utf-8')
    
def create_observer(environ, start_response):
    """
    Create an observer.
    
    observer?type=TYPE,
    """
    start_response('200 OK', [ ('Content-type', 'text/plain') ])
    #params = environ['params']
    yield 'ENVIRON:\n'
    for k, v in environ.iteritems():
        yield 'key: {}  value: {}\n'.format(k, str(environ[k]))
    #yield 'WSGI.INPUT:\n'
    #for k, v in params.iteritems():
        #yield 'key: {}  value: {}\n'.format(k, str(params[k]))
    
if __name__ == '__main__':
    # WSGI path dispatcher recipe from Python Cookbook, 3rd ed.
    # modifications for time series use
    from resty import PathDispatcher
    from wsgiref.simple_server import make_server

    # Create the dispatcher and register functions
    dispatcher = PathDispatcher()
    dispatcher.register('GET', '/hello', hello_world)
    dispatcher.register('GET', '/localtime', localtime)
    dispatcher.register('GET', '/stats/disk', diskstats)
    dispatcher.register('GET', '/ctrl', ctrl)
    dispatcher.register('PUT', '/observer', create_observer)
    
    # spin up the Observer thread for disk stats
    # these globals will be rolled into objects later... or something like that
    global obs, q
    q = Queue()
    obs = StorageObserver('var partition', q, '/var', data_format=CSV_DATA)
    t = Thread(target=obs.run)
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
    discard = 0
    while not q.empty():
        discard += 1
        q.get()
        q.task_done()
    print 'discarded {} queue items'.format(discard)
    q.join()
    print 'shutdown complete'