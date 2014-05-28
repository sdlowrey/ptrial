"""
Record time series data to various kinds of storage facilities.
"""

class RecorderError(Exception):
    pass

class TextFile(object):
    """
    Record data in a text file.
    
    An optional header string can be provided to write useful things like field names, etc.
    """
    def __init__(self, file_obj, header=None):
        """
        Args:
        
          file_obj: file object that is open and writable
          header: string to write before writing data
        """
        self._file = file_obj
        if header:
            self.store(header)
        
    def store(self, data):
        """
        Write the data with a trailing newline.
        """
        self._file.write('{}\n'.format(data))
