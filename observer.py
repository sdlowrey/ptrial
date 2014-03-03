# Max line length = 100                                                                            1
#        1         2         3         4         5         6         7         8         9         0
#234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890

import json
import time

# Constants
OBS_TIME_STRING_FORMAT  = '%Y-%m-%d %H:%M:%S'
OBS_TIME_FORMAT_INTEGER = 1
OBS_TIME_FORMAT_ASCII   = 2

OBS_ENCODE_JSON = 1
OBS_ENCODE_PYTHON = 2

# Exception messages
OBS_NAME_ERR = 'An observer must have a name'

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
    
    def __init__(self, name=None, time_format=OBS_TIME_FORMAT_INTEGER):
        """
        Check the name and determine the time formatting function to use.
        
        Args:
          name: the name of this observer; preferably a string
          time_enc: integer (default) or ASCII; use OBS_TIME_* constants.
        """
        # Raise an error if caller did not specify or if type can't be converted
        if not name:
            raise ObserverError(OBS_NAME_ERR)
        self.name = str(name)
        
        self._time = self._integer_time
        if time_format == OBS_TIME_FORMAT_ASCII:
            self._time = self._ascii_time
            
        self._source = None
        self._datapoint = None

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
        Retrieve a datapoint. The datapoint is stored as a "native" attribute of the caller but is
        returned to the caller as an encoded (serialized) object.
        """
        self.open_source()
        self._datapoint = { self._time() : self.read_source() }
        self.close_source()
        return self._encode(self._datapoint)

    def _ascii_time(self):
        return time.strftime(OBS_TIME_STRING_FORMAT)
    
    def _integer_time(self):
        return int(time.time())
    
    def _encode(self, data):
        """
        Encode a data object into JSON structure. Subclasses may override.
        """
        return json.dumps(data)
