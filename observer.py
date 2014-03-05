
import json
from Queue import Queue
import time

# Constants
OBS_TIME_STRING_FORMAT  = '%Y-%m-%d %H:%M:%S'
OBS_INTEGER_TIME = 1
OBS_ASCII_TIME   = 2

OBS_JSON_DATA = 1
OBS_PYTHON_DATA = 2

# Exception messages
OBS_INVALID_NAME = 'An observer must have a name'
OBS_INVALID_INTERVAL = 'Loop observer interval must be >= 1 second'
OBS_INVALID_ARG = 'Argument {} is an invalid type'

class ObserverError(Exception):
    pass

class ObserverBase(object):
    """
    Record observations obtained from a data source.  
    
    This is a base class that provides simple read-once functionality. Subclasses should override
    the *_source methods.
    
    Attributes:
      name: name of the observer
    """
    
    def __init__(self, name, time_format=OBS_INTEGER_TIME, data_format=OBS_PYTHON_DATA):
        """
        Check the name and determine the time formatting function to use.
        
        Args:
          name: the name of this observer; must be a string or have a string representation
          time_enc: optional encoding format integer or ASCII; use OBS_TIME_* constants.
        """
        if not name:
            raise ObserverError(OBS_INVALID_NAME)
        self.name = str(name)
        self._time = self._integer_time
        if time_format == OBS_ASCII_TIME:
            self._time = self._ascii_time
            
        self._source = None
        self._datapoint = None
        self._data_format = data_format

    def open_source(self):
        """
        Open the data source being observed.
        """
        pass
    
    def read_source(self):
        """
        Read data from the observed source. This method should be overridden by subclasses.
        
        Note that this method handles data. It is not concerned with time/timestamps.
        
        Returns:
          A dictionary of metric names and values.  The value can be any object type.
        """
        return { 'test' : None }
    
    def close_source(self):
        """
        Close the file or connection. Subclasses that override this method should call the base
        method after doing their own work.
        """
        self._source = None
        
    def get_datapoint(self):
        """
        Retrieve a datapoint. Data format depends on self._data_format.
        """
        self.open_source()
        self._datapoint = { self._time() : self.read_source() }
        self.close_source()
        if self._data_format == OBS_PYTHON_DATA:
            return self._datapoint
        # Note that this does not change the datapoint itself
        return json.dumps(self._datapoint)

    def _ascii_time(self):
        return time.strftime(OBS_TIME_STRING_FORMAT)
    
    def _integer_time(self):
        return int(time.time())

class LoopObserver(ObserverBase):
    """
    Record observations at regular intervals and place data into a queue.
    
    Objects of this type should run in a thread. The caller creates the queue passes it to the
    observer during init.
    """
        
    def run(self, outq, interval=1):
        """
        Continually place observed data into the queue.        
        """
        self._run = True
        while self._run:
            outq.put(self.get_datapoint())
            time.sleep(interval)

    def stop(self):
        self._run = False
