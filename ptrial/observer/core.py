"""
The core module provides the fundamental interfaces for getting time-series data from a source.
"""
from collections import OrderedDict
import datetime
import json
import os.path
from Queue import Queue
import random
import re
import string
import subprocess
import time

# Public data format constants
JSON_DATA   = 1
PYTHON_DATA = 2
CSV_DATA    = 3

# Public time format constants
TIME_STRING_FORMAT  = '%Y-%m-%d %H:%M:%S'
INTEGER_TIME = 1
ASCII_TIME   = 2

# Private constants
_INVALID_ARG      = 'Argument {} is an _INVALID type'
_INVALID_INTERVAL = 'Loop observer interval must be >= 1 second'
_INVALID_NAME     = 'An observer must have a name'
_NO_QUEUE = 'No output queue set for observer' 

class ObserverError(Exception):
    pass

class ObserverBase(object):
    """
    ObserverBase provides the basic interaction for datapoint processing.  It is not intended to
    be used by client programs.  Subclasses must override the _read_source method.

    Timestamps can be encoded as seconds-from-epoch (integer) or string (Y-m-d H:M:S).  Use
    the INTEGER_TIME and ASCII_TIME constants to choose.  The default is INTEGER_TIME.

    Data can be returned as a Python dictionary, JSON object, or CSV text (one line).  Use the
    *_DATA constants to choose.  CSV data will be returned in 
        
    Constructor args:

          name:        the name of this observer; must be a string or have a string representation
          time_format: encoding format for timestamps
          data_format: encoding format for data collections
          time_as_key: timestamp is a key (data map is the value) for use in column family DBs; if
                       set to False, then time is a value for the key 'timestamp'
                       (see http://www.datastax.com/dev/blog/advanced-time-series-with-cassandra)
    
    Attributes:
    
      name: name of the observer
      datapoint: the most recent datapoint
      field_names: ordered sequence of field (metric) names
      
    """
    
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA, time_as_key=True):
        """
        Check the name and determine the time formatting function to use.
        
        """
        if not name:
            raise ObserverError(_INVALID_NAME)
        self.name = str(name)
        self._time_as_key = time_as_key
        self._time = self._integer_time
        if time_format == ASCII_TIME:
            self._time = self._ascii_time
            self._time_as_key = False
        self._data_format = data_format
        encoder = {
            JSON_DATA: self._json_data,
            PYTHON_DATA: self._python_data,
            CSV_DATA: self._csv_data
        }
        self._encode = encoder[data_format]

        # Field (metric) names and their optional string indexes must be defined in subclasses.
        self._field_names = ()
        self._field_indexes = ()
        self._datapoint = None
            
    def get_datapoint(self):
        """
        Retrieve a datapoint with the correct encoding applied.
        """
        if self._time_as_key:
            self._datapoint = { 'name': self.name, self._time() : self._read_source() }
        else:
            self._datapoint = {'name': self.name, 'time': self._time(), 'data': self._read_source()}
        return self._encode(self._datapoint)
    
    @property
    def datapoint(self):
        """The current datapoint as a dictionary object.
        
        This property's initial purpose is to enhance the testability of Observer objects.
        """
        return self._datapoint

    @property
    def field_names(self):
        """
        The names of each of field or metric in the datapoint.  If the selected data format is CSV,
        then the return value is a CSV string that can be used as a header.
        
        Field names are equivalent to the keys for individual metrics when using Python or JSON 
        datapoint formats."""
        if self._data_format is CSV_DATA:
            return 'timestamp,' + ','.join(self._field_names)
        else:
            return self._field_names
    
    def _read_source(self):
        """
        Read data from the observed source.
        
        This method handles data only. It is not concerned with time/timestamps.

        Subclasses must override this method.  They need to manage the connection to the data
        source themselves.  Some classes may want to open and close the source during each call.
        Others may open the source once and leave it open.
        
        Returns:
          A dictionary of metric names and values.  The value can be any object type.
        """
        raise NotImplementedError

    def _ascii_time(self):
        return time.strftime(TIME_STRING_FORMAT)
    
    def _integer_time(self):
        return int(time.time())    

    def _csv_data(self, data):
        """
        Reformat data as a CSV string.
        
        NOTE: use of data formatters here is discouraged.  It's better if the caller can handle
        this chore.
        
        Output consists only of the timestamp and the item values.  The timestamp is 
        always the first field.  Because the data is stored in an OrderedDict, the values are 
        returned in the order of the keys as they are defined in the subclass *_DATA tuples. 
        
        Args:
          data: a Python dictionary containing data items only (i.e., not a complete datapoint)
        """
        # (Because timestamp is a key (and thus constantly changes) the writers in the Python csv
        # module aren't of much use.  
        ts = None
        if not self._time_as_key:
            ts = data['time']
        else:                    
            # find the integer timestamp, which is a key
            for k in data.keys():
                if type(k) is int:
                    ts = k
                
        line = str(ts)
        for k in self._field_names:
            metric = str(data[ts][k]) if self._time_as_key else str(data['data'][k])
            line = line + ',' + metric
        return line
    
    def _json_data(self, data):
        """
        Reformat datapoint as a JSON-formatted string 
        
        NOTE: use of data formatters here is discouraged.  It's better if the caller can handle
        this chore.

        Args:
          data: a Python dictionary
        """
        return json.dumps(data)
    
    def _python_data(self, data):
        """
        No formatting done.  Simply return the data as-is. 
        
        Args:
          data: a Python dictionary containing data items only (i.e., not a complete datapoint)
        """
        return data
    
class TestObserver(ObserverBase):
    """
    A one-shot observer that generates a single fake datapoint.
    """
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA, time_as_key=True):
        super(TestObserver, self).__init__(name, time_format, data_format, time_as_key)
        self._field_names = ('thing1', 'thing2')

    def _read_source(self):
        data = OrderedDict()
        for thing in self._field_names:
            data[thing] =  random.randint(1,999999)
        return data

class QueueObserver(ObserverBase):
    """
    Make observations at regular intervals and place data into a queue.
    
    Objects of this type should run in a thread. The caller creates the queue passes it to the
    observer during init:
    
    Example:
        input_q = Queue()
        obs = observer.LoopObserver('looper')
        thread = Thread(target=obs.run, args=(input_q,))
        thread.start()
    Args:
          outq: output queue for datapoints [default is None]
          interval: sleep interval in seconds between datapoints; default is 1 second
          count: number of datapoints to read, default 0 (no limit); used for unit testing
    """
    def __init__(self, name, queue=None, interval=1, count=0, time_format=INTEGER_TIME, 
                 data_format=PYTHON_DATA, time_as_key=True):
        super(QueueObserver, self).__init__(name, time_format, data_format, time_as_key)
        self._queue = queue
        self._interval = interval
        self._count = count
        self._run = True
        self._start_time = datetime.datetime.now()
        self.end_data = object()  # dummy object to put in the queue to indicate EOD
        
    def run(self):
        """
        Continually place observed data into the queue until the stop() method is called.
        If the optional count parameter is specified, read N times or until stop().
        
        Use this method as a run target for a Thread object.
        """
        if not self._queue:
            raise ObserverError(_NO_QUEUE)
        
        counting = True if self._count > 0 else False

        while self._run and (self._count > 0 or not counting):
            if counting:
                self._count -= 1
            # FIXME: caller should  set maxsize, so set timeout and handle Queue.Full (data gap)
            self._queue.put(self.get_datapoint())
            time.sleep(self._interval)
        self._queue.put(self.end_data)
        
    @property
    def queue(self):
        """
        Get the output queue for this observer.
        """
        return self._queue

    @queue.setter
    def queue(self, q):
        self._queue = q
        
    @queue.deleter
    def queue(self):
        del self._queue
        
    def status(self):
        """
        Report on queue size and run time.
        """
        if not self._queue:
            raise ObserverError(_NO_QUEUE)

        now = datetime.datetime.now()
        state = {
            'interval': self._interval,
            'qsize': self._queue.qsize(),
            'uptime': str(now - self._start_time),
        }
        return state

    def stop(self):
        """
        Stop the observer on the next iteration.
        """
        if not self._queue:
            raise ObserverError(_NO_QUEUE)
        
        self._run = False

class TestQueueObserver(QueueObserver):
    """
    A loop server that generates random data for testing.
    """
    def __init__(self, name, queue, interval=1, count=0, time_format=INTEGER_TIME, 
                 data_format=PYTHON_DATA, time_as_key=True):
        super(TestQueueObserver, self).__init__(name, queue, interval, count, time_format, 
                                               data_format, time_as_key)
        self._field_names = ('test',)
        
    def _read_source(self):
        data = { self._field_names[0] : random.randint(1,999999) }
        return data
