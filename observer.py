
import json
from Queue import Queue
import random
import time

# Constants
OBS_TIME_STRING_FORMAT  = '%Y-%m-%d %H:%M:%S'
OBS_INTEGER_TIME = 1
OBS_ASCII_TIME   = 2

OBS_JSON_DATA = 1
OBS_PYTHON_DATA = 2
OBS_CSV_DATA = 3

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

        # Map numeric data formats to methods
        encoder = {
            OBS_JSON_DATA: self._json_data,
            OBS_PYTHON_DATA: self._python_data,
            OBS_CSV_DATA: self._csv_data
        }
        self._encode = encoder[data_format]

        self._source = None
        self._datapoint = None
            
    def get_datapoint(self):
        """
        Retrieve a datapoint. Data format depends on self._data_format.
        """
        self._datapoint = { 'name': self.name, self._time() : self._read_source() }
        return self._encode()

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
        pass

    def _ascii_time(self):
        return time.strftime(OBS_TIME_STRING_FORMAT)
    
    def _integer_time(self):
        return int(time.time())
    
    def _csv_data(self):
        return self._datapoint

    def _json_data(self):
        return json.dumps(self._datapoint)

    def _python_data(self):
        return self._datapoint
    

class LoopObserver(ObserverBase):
    """
    Record observations at regular intervals and place data into a queue.
    
    Objects of this type should run in a thread. The caller creates the queue passes it to the
    observer during init:
    
    Example:
        input_q = Queue()
        obs = observer.LoopObserver('looper')
        obs_thread = Thread(target=obs.run, args=(input_q,))
        obs_thread.start()
    """
    def run(self, outq, interval=1, count=0):
        """
        Continually place observed data into the queue. Reads until the stop() method is called.
        If the optional count parameter is specified, read N times or until stop().
        
        Args:
          outq: output queue for datapoints
          interval: sleep interval in seconds between datapoints; default is 1 second
          count: number of datapoints to read; defaults to 0 (no limit)
        """
        self._run = True
        counting = False
        if count > 0:
            counting = True
        else:
            count = 1
        self._end_data = object()
        while self._run and count > 0:
            if counting:
                count -= 1
            outq.put(self.get_datapoint())
            time.sleep(interval)
        outq.put(self._end_data)

    def stop(self):
        self._run = False

class TestLoopObserver(LoopObserver):
    """
    A loop server that generates random data for testing.
    
    Does not require open_source or close_source overrides.
    """
    def _read_source(self):
        return { 'test' : random.randint(1,999999) }

class StorageObserver(LoopObserver):
    """
    Get the block I/O stats for a device.
    """
    # https://www.kernel.org/doc/Documentation/iostats.txt
    BLOCK_STAT_FMT = ('rd_comp', 'rd_mrgd', 'rd_blk', 'rd_tm', 'wr_comp', 'wr_mrgd', 'wr_blk',
                      'wr_tm', 'io_prog', 'io_tm','io_tmw')
    
    def __init__(self, name, dev, time_format=OBS_INTEGER_TIME, data_format=OBS_PYTHON_DATA):
        super(StorageObserver, self).__init__(name, time_format, data_format)
        self._device = dev
    
    def _read_source(self):
        f = open('/sys/block/{}/stat'.format(self._device))
        statline = f.readline().strip()
        f.close()
        data = dict(zip(StorageObserver.BLOCK_STAT_FMT, statline.split()))
        return data

class ObservationManager(object):
    def __init__(self, fmt):
        self.set_data_format(fmt)

    def set_data_format(self, fmt):
        """
        Change the data format on the fly.
        """
        encoder = {
            OBS_JSON_DATA: self._json_data,
            OBS_PYTHON_DATA: self._python_data,
            OBS_CSV_DATA: self._csv_data
        }
        self._encode = encoder[fmt]
        
    def store(self, data):
        print self._encode(data)
    
    def _csv_data(self, data):
        """
        Reformat a datapoint as a CSV string.
        
        Because timestamp is a key (and thus constantly changes) the writers in the Python csv
        module aren't of much use.  It's easy enough to handle here, though.
        """
        # the trick here is to find the timestamp key
        for k in data.keys():
            if type(k) is int:
                ts = k
                
        print 'file?: {}'.format(data['name'])
        line = str(ts)
        for k in data[ts].keys():
            line = line + ',' + str(data[ts][k])
        return line
    
    def _json_data(self, data):
        return json.dumps(data)
    
    def _python_data(self, data):
        return data

if __name__ == '__main__':
    data = {'name': 'buddy', 12345: {'metric1': 1231, 'metric2': 989}}
    
    om = ObservationManager(OBS_JSON_DATA)
    om.store(data)
    om.set_data_format(OBS_PYTHON_DATA)
    om.store(data)
    om.set_data_format(OBS_CSV_DATA)
    om.store(data)    
