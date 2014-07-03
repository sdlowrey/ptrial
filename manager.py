"""
The manager is responsible for creating Observers and handling their data streams. 

The manager uses trial context to define the observation and data storage strategies.  Trial context
consists of the following:

  Run strategy: manual stop, stop time, run duration, event-based stop, event + lag interval
  
  Observer parameters
    name, type
    required type parameters (e.g. polling interval, storage device)
    optional time and data format parameters
"""


# first crack: hardcode the parameters, write the streams to named files
# the manager creates the main queue and the observers

import context
import em7_config

class NodeManager(object):
    """
    Manages observation, transformation, and storage for a single node. 
    
    Args:
      context: the TrialContext object for this test
    """
    def __init__(self, trial_ctxt):
        self._trial_ctxt = trial_ctxt
        self._hw_ctxt = context.HardwareContext()
        self._os_ctxt = context.OperatingSystemContext()
        self._init_app_context()        
        
    def _init_app_context(self):
        """
        Capture application-specific context.  This should be overridden in subclasses
        that manage application nodes.
        """
        pass
        
class StoreManager(object):
    """
    Base class for data storage management.
    """
    pass

class FileManager(StoreManager):
    """
    Arranges data storage in files and directories.  Directory hierarchy is ordered by trial,
    node, and app version, and, if there is more than one type of application function, the app
    function.
    
    Each directory contains a context file relevant to that directory: trial, node app.
    
    The application/function directory contains files named by observer class: cpu, storage,
    harvest, etc.  Those directories contain the actual data files: metrics, harvests, etc.
    
    Data files are named according to an archival strategy: hourly, daily, size limit, etc.
    
    trial/node/node-name/
    """
    pass