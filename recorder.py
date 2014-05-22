"""
Record time series data to various kinds of storage facilities.
"""
import encoder

class RecorderError(Exception):
    pass

class TextFile(object):
    """
    Record data in a text file.
    """
    def __init__(self, file_obj, encoder):
        """
        Args:
        
          file_obj: file object that is open and writable
          
          encoder: Encoder object that is configured to format any textual data
        """
        self._file = file_obj
        self._enc = encoder

            
    def store(self, data):
        with self._file as f:
            f.write(self._enc.encode(data))
        
