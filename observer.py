from collections import OrderedDict
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
_INVALID_PATH     = 'No such path "{}"'
_PATH_PART_NOT_FOUND = 'Partition for "{}" directory not found'
_PID_NOT_FOUND    = 'Process {} not found'

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
    
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA):
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
            
    def get_datapoint(self):
        """
        Retrieve a datapoint with the correct encoding applied.
        """
        self._datapoint = { 'name': self.name, self._time() : self._read_source() }
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
        Reformat data as a JSON object 
        
        Args:
          data: a Python dictionary containing data items only (i.e., not a complete datapoint)
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
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA):
        super(TestObserver, self).__init__(name, time_format, data_format)
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
    """
    def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA):
        super(TestLoopObserver, self).__init__(name, time_format, data_format)
        self._field_names = ('test',)
        
    def _read_source(self):
        data = { self._field_names[0] : random.randint(1,999999) }
        return data

class StorageObserver(LoopObserver):
    """
    Get the block I/O stats for a device.
    """
    # https://www.kernel.org/doc/Documentation/iostats.txt
    
    def __init__(self, name, dev=None, time_format=INTEGER_TIME, data_format=PYTHON_DATA):
        super(StorageObserver, self).__init__(name, time_format, data_format)
        self._device = dev
        self._path = None
        self._field_names = ('rd_comp', 'rd_mrgd', 'rd_blk', 'rd_tm', 'wr_comp', 'wr_mrgd', 
                             'wr_blk', 'wr_tm', 'io_prog', 'io_tm', 'io_tmw')
        
    def set_device(self, path):
        """
        Observe the partition that is associated with a directory.
        
        TODO: handle more args and tie in to the constructor
        
        Args:
          path: directory
        """
        if not os.path.exists(path):
            raise ObserverError(_INVALID_PATH.format(path))
        self._path = path
        self._get_partition_dev(path)
        
    def _get_partition_dev(self, path):
        """
        Get the partition device associated with a path
        """
        # build a dict of mountpoints and their device names
        mountpoint = {}
        mounts = subprocess.check_output(['mount']).split('\n')
        for mount in mounts:
            fields = mount.split()
            if not fields:
                continue
            mountpoint[fields[2]] = fields[0]

        previous = ''
        while path != previous:
            if path in mountpoint.keys():
                # we have the partition; get the real device file if it's a symlink
                try:
                    realdev = os.readlink(mountpoint[path])
                    self._device = os.path.basename(realdev)
                except OSError:
                    # it's not a symlink
                    self._device = os.path.basename(mountpoint[path])
                return
            previous = path
            path = os.path.dirname(path)
        raise ObserverError(_PATH_PART_NOT_FOUND.format(self._path))
  
    def _read_source(self):
        """Get the metrics for the device and put them into a dictionary.
        """
        # Block device trees vary a little.  If the newer path doesn't work, try the older
        # one (2.6.18 era).  If that doesn't work, open() will toss IOError.
        devpath = '/sys/block/{}/stat'.format(self._device)
        if not os.path.exists(devpath):
            devpath =  '/sys/block/{}/{}/stat'.format(self._device.rstrip(string.digits),
                                                      self._device)
        with open(devpath) as f:
            statline = f.readline().strip()
        data = OrderedDict(zip(self._field_names, statline.split()))
        return data

class ProcessObserver(LoopObserver):
    """
    Get stats for a process/task.
    
    The returned data is a dict containing the following items:
    
      state     One character from the string "RSDZTW" where R is running, S is sleeping in an
                interruptible wait, D is waiting in uninterruptible disk sleep, Z is zombie,
                T is traced or stopped (on a signal), and W is paging.
               
      minflt    The number of minor faults the process has made which have not required loading a
                memory page from disk.
               
      cminflt   The number of minor faults that the process's waited-for children have made.
      
      majflt    The number of major faults the process has made which have required loading a
                memory page from disk.
          def __init__(self, name, time_format=INTEGER_TIME, data_format=PYTHON_DATA):
      cmajflt   The number of major faults that the process's waited-for children have made.

      utime     Amount of time that this process has been scheduled in user mode, measured in
                clock ticks (divide by sysconf(_SC_CLK_TCK)).  This includes guest_time (time
                spent running a virtual CPU) so that applications that are not aware of the guest
                time field do not lose that time from their calculations.

      stime     Amount of time that this process has been scheduled in kernel mode, measured in
                clock ticks (divide by sysconf(_SC_CLK_TCK)).

      priority  For processes running a real-time scheduling policy, this is the negated
                scheduling priority, minus one; that is, a number in the range -2 to -100,
                corresponding to real-time priorities 1 to 99.  For processes running under a
                non-real-time scheduling policy, this is the raw nice value (setpriority(2)) as
                represented in the kernel.  The kernel stores nice values as numbers in the range
                0 (high) to 39 (low), corresponding to the user-visible nice range of -20 to 19.
                
      rss       Resident Set Size: number of pages the process has in real memory.  This is just
                the pages which count toward text, data, or stack space.  This does not include
                pages which have not been demand-loaded in, or which are swapped out.

      nthreads  Number of threads in this process.
    
    Items like start time and name are not returned because they never change.  The caller
    can get those bits of static info from utility functions.
    
    See http://man7.org/linux/man-pages/man5/proc.5.html for complete details.
    """
    
    # To add another statistic, update _field_* tuples.  The index numbers are available in the
    # proc(5) man page.  Remember zero-based: subtract 1 to match indexes shown in man page.
    
    def __init__(self, name, pid=None, time_format=INTEGER_TIME):
        super(ProcessObserver, self).__init__(name, time_format)
        self._field_names = ('state', 'minflt', 'cminflt', 'majflt', 'cmajflt', 'utime', 'stime',
                             'priority', 'nthreads', 'rss')
        self._field_indexes = (2, 9, 10, 11, 12, 13, 14, 17, 19, 23)
        self._pid = pid
        
    def _read_source(self):
        statpath = '/proc/{}/stat'.format(self._pid)
        if not os.path.exists(statpath):
            raise ObserverError(_PID_NOT_FOUND.format(self._pid))
        
        with open(statpath) as f:
            statline = f.readline().strip()
        stat_list =  statline.split()
        stats = []
        for i in self._field_indexes:
            stats.append(stat_list[i])
        data = OrderedDict(zip(self._field_names, stats))
        return data
