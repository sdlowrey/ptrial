"""
Containers for various read-only classes of configuration data.
"""
import collections
import os
import socket

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
    def _populate(self):
        items = self._items
        items['hostname'] = socket.gethostname()
        items['kernel'] = os.uname()[2]
        
