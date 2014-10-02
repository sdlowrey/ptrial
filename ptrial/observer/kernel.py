"""
The observer.kernel modules gathers continuous kernel metrics.  These metrics are sourced from 
/proc and /sys.
"""
from collections import OrderedDict
from ptrial.observer.core import LoopObserver, INTEGER_TIME, PYTHON_DATA
import os
import os.path
import string
import subprocess

# Private constants
_INVALID_PATH     = 'No such path "{}"'
_PATH_PART_NOT_FOUND = 'Partition for "{}" directory not found'
_PID_NOT_FOUND    = 'Process {} not found'


class StorageObserver(LoopObserver):
    """
    Get the block I/O stats for a device.
    """
    # https://www.kernel.org/doc/Documentation/iostats.txt
    
    def __init__(self, name, queue, path=None, interval=1, count=0, time_format=INTEGER_TIME, 
                 data_format=PYTHON_DATA, time_as_key=True):
        super(StorageObserver, self).__init__(name, queue, interval, count, time_format, 
                                              data_format, time_as_key)
        if not os.path.exists(path):
            raise ObserverError(_INVALID_PATH.format(path))
        self._path = path
        self._block_device = self._find_block_device()
        self._device_stats = self._find_stat_path()
        self._field_names = ('rd_comp', 'rd_mrgd', 'rd_blk', 'rd_tm', 'wr_comp', 'wr_mrgd', 
                             'wr_blk', 'wr_tm', 'io_prog', 'io_tm', 'io_tmw')        

    def _find_block_device(self):
        """
        Get the block device associated with a path (directory).  Any path can be provided; it does
        not have to be the the top-level directory at which a block device is mounted.
        """
        # build a dict of mountpoints (directory) and device names
        # 'mount' output looks like this:
        #     /dev/vda9 on /data.local type xfs (rw,noatime)
        mountpoint = {}
        mounts = subprocess.check_output(['mount']).split('\n')
        for mount in mounts:
            fields = mount.split()
            if not fields:
                continue
            mountpoint[fields[2]] = fields[0]

        # search all mountpoints for the path, recursing backward through the path name if necessary
        path = self._path
        previous = ''
        while path != previous:
            if path in mountpoint.keys():
                # we have the partition; get the real device file if it's a symlink
                try:
                    realdev = os.readlink(mountpoint[path])
                    blockdev = os.path.basename(realdev)
                except OSError:
                    # it's not a symlink
                    blockdev = os.path.basename(mountpoint[path])
                return blockdev
            # go back one level in the path
            previous = path
            path = os.path.dirname(path)
        raise ObserverError(_PATH_PART_NOT_FOUND.format(self._path))
    
    def _find_stat_path(self):
        """
        Find the path to the device stats in sysfs
        """
        # Block device trees vary a little.  If the newer path doesn't work, try the older
        # one (2.6.18 era).  If that doesn't work, open() will raise IOError.
        stat_path = '/sys/block/{}/stat'.format(self._block_device)
        if not os.path.exists(stat_path):
            stat_path = '/sys/block/{}/{}/stat'.format(self._block_device.rstrip(string.digits),
                                                       self._block_device)
        return stat_path
  
    def _read_source(self):
        with open(self._device_stats) as f:
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
                the pages which count toward text, data, or stack name, queue, interval, count, time_format, 
                                              data_format, time_as_keyspace.  This does not include
                pages which have not been demand-loaded in, or which are swapped out.

      nthreads  Number of threads in this process.
    
    Items like start time and name are not returned because they never change.  The caller
    can get those bits of static info from utility functions.
    
    See http://man7.org/linux/man-pages/man5/proc.5.html for complete details.
    """
    
    # To add another statistic, update _field_* tuples.  The index numbers are available in the
    # proc(5) man page.  Remember zero-based: subtract 1 to match indexes shown in man page.
    
    def __init__(self, name, queue, pid=None, interval=1, count=0, time_format=INTEGER_TIME, 
                 data_format=PYTHON_DATA, time_as_key=True):
        super(ProcessObserver, self).__init__(name, queue, interval, count, time_format, 
                                              data_format, time_as_key)
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
