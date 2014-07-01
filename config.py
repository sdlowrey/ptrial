"""
Containers for various read-only classes of configuration data.
"""
import collections
import os
import socket

CPU_FILE = '/proc/cpuinfo'

HOSTNAME = 'hostname'
KERNEL = 'kernel'
CPU_MODEL = 'cpu_model'
CPU_NCORES = 'cpu_ncores'

class ConfigurationBase(collections.Mapping):
    """
    A base class that implements an immutable mapping container.
    
    The _populate method is overridden by subclasses to create items in the map.
    """
    def __init__(self):
        self._items = {}
        self._populate()
        
    def __getattr__(self, key):
        return self._items[key]
    
    def __getitem__(self, key):
        return self._items[key]
    
    def __iter__(self):
        return iter(self._items)
    
    def __len__(self):
        return len(self._items)
    
    def _populate(self):
        raise NotImplemented
    
class OperatingSystemConfiguration(ConfigurationBase):
    """
    General OS attributes.  
    """
    def _populate(self):
        items = self._items
        items[HOSTNAME] = socket.gethostname()
        items[KERNEL] = os.uname()[2]

class HardwareConfigurationError(Exception):
    """
    An error occurred while getting the hardware configuration
    """
    pass

class HardwareConfiguration(ConfigurationBase):
    """
    General hardware attributes.
    """
    # techniques here are crude.  see https://git.fedorahosted.org/cgit/python-dmidecode.git
    
    def __init__(self, cpufile=CPU_FILE):
        """
        Allow the caller to specify test files.
        """
        self._cpu_file = cpufile
        super(HardwareConfiguration, self).__init__()

    def _populate(self):
        self._cpu_info()
    
    def _cpu_info(self):
        """
        Parse CPU info from /proc/cpuinfo.
        """
        with open(self._cpu_file) as f:
            lines = f.readlines()

        wanted_attrs = {'model name': None, 'cpu cores': None}
        for line in lines:
            l = line.split(':')
            for k in wanted_attrs.keys():
                if l[0].strip() == k:
                    wanted_attrs[k] = l[1].strip()
        for k, v in wanted_attrs.iteritems():
            if v is None:
                raise HardwareConfigurationError(self._err_missing_value(k))
        self._items[CPU_MODEL] = wanted_attrs['model name']
        self._items[CPU_NCORES] = int(wanted_attrs['cpu cores'])

    def _err_missing_value(self, key):
        return 'value for key "{}" not found'.format(key)