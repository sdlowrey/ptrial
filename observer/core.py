"""
The observer module contains the base Observer classes and specialized subclasses.
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

class ObserverError(Exception):
    pass

class ObserverBase(object):
    """
    Record observations obtained from a data source.  
    
    This is a base class that provides simple read-once functionality. Subclasses should override
    the read_source method.
    
    Attributes:
      name: name of the observer
      
      datapoint: the most recent datapoint
    """
    
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA, time_as_key=True):
        """
        Check the name and determine the time formatting function to use.
        
        Timestamps can be encoded as seconds-from-epoch (integer) or string (Y-m-d H:M:S).  Use
        the INTEGER_TIME and ASCII_TIME constants to choose.  The default is INTEGER_TIME.
        
        Data can be returned as a Python dictionary, JSON object, or CSV text (one line).  Use the
        *_DATA constants to choose.  CSV data will be returned in 
        
        Args:

          name: the name of this observer; must be a string or have a string representation

          time_format: encoding format for timestamps

          data_format: encoding format for data collections

          time_as_key: timestamp is a key (data map is the value) for use in column family DBs
                       (see http://www.datastax.com/dev/blog/advanced-time-series-with-cassandra)
        """
        if not name:
            raise ObserverError(_INVALID_NAME)
        self.name = str(name)
        self._time = self._integer_time
        if time_format == ASCII_TIME:
            self._time = self._ascii_time
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
        self._time_as_key = time_as_key
            
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
        """A tuple of data field (metric) names.  
        
        Field names are equivalent to the keys for individual metrics when using Python or JSON 
        datapoint formats."""
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
        Reformat data as a CSV string
        
        Output consists only of the timestamp and the item values.  The timestamp is 
        always the first field.  Because the data is stored in an OrderedDict, the values are 
        returned in the order of the keys as they are defined in the subclass *_DATA tuples. 
        
        Args:
          data: a Python dictionary containing data items only (i.e., not a complete datapoint)
        """
        # (Because timestamp is a key (and thus constantly changes) the writers in the Python csv
        # module aren't of much use.  It's not a problem here, but consider making timestamp a value
        # with its own key in the future.)
                
        # find the timestamp key
        for k in data.keys():
            if type(k) is int:
                ts = k
                
        line = str(ts)
        for k in self._field_names:
            line = line + ',' + str(data[ts][k])
        return line
    
    def _json_data(self, data):
        """
        Reformat datapoint as a JSON-formatted string 
        
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

class LoopObserver(ObserverBase):
    """
    Make observations at regular intervals and place data into a queue.
    
    Objects of this type should run in a thread. The caller creates the queue passes it to the
    observer during init:
    
    Example:
        input_q = Queue()
        obs = observer.LoopObserver('looper')
        thread = Thread(target=obs.run, args=(input_q,))
        thread.start()
    """
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA, time_as_key=True):
        super(LoopObserver, self).__init__(name, time_format, data_format, time_as_key)
        self._queue = outq
        self._interval = interval
        self._count = count
        self._run = True
        self._start_time = datetime.datetime.now()
        self.end_data = object()  # dummy object to put in the queue to indicate EOD
        
    def run(self, outq, interval=1, count=0):
        """
        Continually place observed data into the queue. Reads until the stop() method is called.
        If the optional count parameter is specified, read N times or until stop().
        
        Args:
          outq: output queue for datapoints
          interval: sleep interval in seconds between datapoints; default is 1 second
          count: number of datapoints to read; defaults to 0 (no limit)
        """

        # TODO: can probably throw out this test-only counting mechanism
        counting = False
        if count > 0:
            counting = True
        else:
            count = 1

        while self._run and count > 0:
            if counting:
                count -= 1
            # FIXME: caller should  set maxsize, so set timeout and handle Queue.Full (data gap)
            outq.put(self.get_datapoint())
            time.sleep(interval)
        outq.put(self.end_data)
        
    def status(self):
        """
        Report on queue size and run time.
        """
        now = datetime.datetime.now()
        state = {
            'interval': self._interval,
            'qsize': self._queue.qsize(),
            'uptime': str(now - self._start_time),
        }
        return state

    def stop(self):
        self._run = False

class TestLoopObserver(LoopObserver):
    """
    A loop server that generates random data for testing.
    """
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA):
        super(TestLoopObserver, self).__init__(name, time_format, data_format)
        self._field_names = ('test',)
        
    def _read_source(self):
        data = { self._field_names[0] : random.randint(1,999999) }
        return data