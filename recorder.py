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
    def __init__(self, file_obj, enc):
        """
        Args:
        
          file_obj: file object that is open and writable
          
          enc: Encoder object that is configured to format any textual data
        """
        self._file = file_obj
        self._enc = enc
        self.header(self._enc.encode_header())
            
    def header(self, data):
        self._file.write('{}\n'.format(data))
        
    def store(self, data):
        self._file.write('{}\n'.format(self._enc.encode(data)))
