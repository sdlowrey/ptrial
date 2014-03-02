import time

class ObserverError(Exception):
    pass

class ObserverBase(object):
    """
    Record observations obtained from a data source.  
    
    This base class provides simple read-once functionality.
    
    Attributes:
      open_source:  create a connection or open a file
      close_source: close a connection or file
      read_source:  take a single observation from the source
      transform:    parse the data into a standard structure
    """
    
    def __init__(self):
        self._source = None
        self._series = {}

    def open_source(self):
        """
        Open the data source being observed.  Depending on the mode of access,
        this method may open the source on each call or may verify that an
        existing file or connection is still open.
        """
        pass
    
    def read_source(self):
        """
        Read data from the observed source.
        """
        pass
    
    def _encode(self):
        """
        Encode a data object into a standard (JSON) structure.  Append the
        transformed data to an internal map keyed by timestamp.
        """
        pass
    
    def close_source(self):
        """
        Close the file or connection.
        """
        self._source = None

    def __del__(self):
        """
        Destructor (ref count == 0): close the data source if it is open.
        """
        if self._source:
            self.close_source()
            