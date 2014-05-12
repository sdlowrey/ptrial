
import json
import os.path
from Queue import Queue
import random
import re
import string
import subprocess
import time

# Public constants
TIME_STRING_FORMAT  = '%Y-%m-%d %H:%M:%S'
INTEGER_TIME = 1
ASCII_TIME   = 2

JSON_DATA   = 1
PYTHON_DATA = 2
CSV_DATA    = 3

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
    
    def __init__(self, name, time_format=INTEGER_TIME):
        """
        Check the name and determine the time formatting function to use.
        
        Args:
          name: the name of this observer; must be a string or have a string representation
          time_enc: optional encoding format integer or ASCII; use TIME_* constants.
        """
        if not name:
            raise ObserverError(_INVALID_NAME)
        self.name = str(name)
        self._time = self._integer_time
        if time_format == ASCII_TIME:
            self._time = self._ascii_time

        self._source = None
        self._datapoint = None
            
    def get_datapoint(self):
        """
        Retrieve a datapoint. Data format depends on self._data_format.
        """
        self._datapoint = { 'name': self.name, self._time() : self._read_source() }
        return self._datapoint

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
        return time.strftime(TIME_STRING_FORMAT)
    
    def _integer_time(self):
        return int(time.time())    

class LoopObserver(ObserverBase):
    """
    Record observations at regular intervals and place data into a queue.
    
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
    
    Does not require open_source or close_source overrides.
    """
    def _read_source(self):
        return { 'test' : random.randint(1,999999) }

class StorageObserver(LoopObserver):
    """
    Get the block I/O stats for a device.
    """
    # https://www.kernel.org/doc/Documentation/iostats.txt
    BLOCK_STATS = ('rd_comp', 'rd_mrgd', 'rd_blk', 'rd_tm', 'wr_comp', 'wr_mrgd', 'wr_blk',
                   'wr_tm', 'io_prog', 'io_tm','io_tmw')
    
    def __init__(self, name, dev=None, time_format=INTEGER_TIME):
        super(StorageObserver, self).__init__(name, time_format)
        self._device = dev
        self._path = None
        
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
        data = dict(zip(StorageObserver.BLOCK_STATS, statline.split()))
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
    
    # To add another statistic, update these tuples.  The index numbers are available in the
    # proc(5) man page.
    TASK_STAT_INDEX = (3, 10, 11, 12, 13, 14, 15, 18, 20, 24)
    TASK_STAT_NAMES = ('state', 'minflt', 'cminflt', 'majflt', 'cmajflt', 'utime', 'stime',
                       'priority', 'nthreads', 'rss')
    
    def __init__(self, name, pid=None, time_format=INTEGER_TIME):
        super(ProcessObserver, self).__init__(name, time_format)
        self._pid = pid
        
    def _read_source(self):
        statpath = '/proc/{}/stat'.format(self._pid)
        if not os.path.exists(statpath):
            raise ObserverError(_PID_NOT_FOUND.format(self._pid))
        
        with open(statpath) as f:
            statline = f.readline().strip()
        stat_list =  statline.split()
        stats = []
        for i in ProcessObserver.TASK_STAT_INDEX:
            stats.append(stat_list[i])
        data = dict(zip(ProcessObserver.TASK_STAT_NAMES, stats))
        return data
    
class ObservationManager(object):
    def __init__(self, fmt):
        self.set_data_format(fmt)

    def set_data_format(self, fmt):
        """
        Change the data format on the fly.
        """
        encoder = {
            JSON_DATA: self._json_data,
            PYTHON_DATA: self._python_data,
            CSV_DATA: self._csv_data
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
    
    om = ObservationManager(JSON_DATA)
    om.store(data)
    om.set_data_format(PYTHON_DATA)
    om.store(data)
    om.set_data_format(CSV_DATA)
    om.store(data)    
