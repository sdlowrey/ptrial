"""
Top-level classes for running a trial.
"""
import context
import collections
import datetime
import time
import util

# The version shall increment whenever the stored representation of a Director changes.
DIRECTOR_VERSION = 1

class Director(object):
    """
    The director is responsible for initiating a trial.
    
    The director holds context and control parameters for gathering data across all nodes in
    a test.  It is responsible for creating and controlling Node Managers and receiving summary
    information at the end of the test.
    
    Args:
      name: a name for the 
    """
    def __init__(self, name, descr, email):
        """
        Create the trial context.
        """
        # This should be immutable, like ConfigurationBase
        self._context = {
            'name': name,
            'description': descr,
            'creation_time': datetime.datetime.now(),
            'start_time': None,  # allow future start?
            'contact_email': email,
            'duration': None, 
            'director_version' : DIRECTOR_VERSION,
        }
        self._summary = { 'run_duration': None, }
        self._nodes = []
        self._node_context = {}

    def set_duration(self, duration):
        self._context['duration'] = datetime.timedelta(hours=duration)
        
    def add_node(self, address):
        """
        Add a compute node to the trial.
        
        Args:
          address: primary IP address of node.
        """
        self._nodes.append(util.IPv4Address(address))
        
# TODO: not sure this one is needed...
class DirectorContext(context.ContextBase):
    def __init__(self, name, descr, email, nodes, duration):
        
        self._context = {
            'name': name,
            'description': descr,
            'creation_time': datetime.now(),
            'start_time': None,  # allow future start?
            'contact_email': email,
            'duration': datetime.timedelta(hours=duration), 
            'director_version' : DIRECTOR_VERSION,
        }
