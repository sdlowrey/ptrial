"""
Encode a time series datapoint (Python dictionary).
"""
import json

# Public data format constants
JSON_DATA   = 1
PYTHON_DATA = 2
CSV_DATA    = 3

class KeyOrderError(Exception):
    pass

NO_KEY_ORDER = 'The key order must be defined for CSV encoding'

class Encoder(object):
    def __init__(self, fmt=PYTHON_DATA, key_order=None):
        """Set the encoder format.  Options are JSON_DATA, PYTHON_DATA, and CSV_DATA.
        
        Args:
          fmt: data encoding format; default is PYTHON_DATA (no encoding).

          key_order: sequence of key names used to select and order CSV output
        """
        self.set_format(fmt)
        self._key_order = key_order

    def encode(self, data):
        """Encode data in the format chosen in the last set_format() call.
        
        Args:
          data: a dictionary in the format of a time series data point 
        """
        return self._encode(data)
    
    def set_format(self, fmt):
        """Change the data encoding on-the-fly.
        
        Args:
          fmt: one of the data format constants defined for this module
        """
        encoder = {
            JSON_DATA: self._json_data,
            PYTHON_DATA: self._python_data,
            CSV_DATA: self._csv_data
        }
        self._encode = encoder[fmt]

    def _csv_data(self, data):
        """
        Reformat a datapoint as a CSV string.  Only values from the timestamp key are included.  
        The 'name' value is discarded (name is tracked by caller).
        
        Only the values for the keys in key_list (in that order) are returned.  The timestamp is 
        always the first field.
        
        (Because timestamp is a key (and thus constantly changes) the writers in the Python csv
        module aren't of much use.  It's not a problem here, but consider making timestamp a value
        with its own key in the future.)
        """
        if self._key_order is None:
            raise KeyOrderError(NO_KEY_ORDER)
        
        # find the timestamp key
        for k in data.keys():
            if type(k) is int:
                ts = k
                
        line = str(ts)
        for k in self._key_order:
            line = line + ',' + str(data[ts][k])
        return line
    
    def _json_data(self, data):
        return json.dumps(data)
    
    def _python_data(self, data):
        return data

