"""
This is a vendor-specific configuration class that is maintained separately from config.py
"""
import context
from ConfigParser import ConfigParser
import manager

# pathnames
SILO_CONF = '/etc/silo.conf'
SILO_REL = '/etc/em7-release'

# silo.conf names for configuration parser 
LOCAL = 'LOCAL'

# map keys
IPADDR = 'ipaddress'
DBUSER = 'dbuser'
DBPASS = 'dbpasswd'
DBDIR = 'dbdir'
TYPE = 'model_type'
BASE_VERSION = 'basever'
    
class EM7ContextError(Exception):
    """
    An error occurred while getting the EM7 configuration
    """
    pass

class EM7Context(context.ContextBase):
    """
    A mapping of select "local only" EM7 configuration attributes.
    """
    
    CONFIG_NOT_FOUND =  'configuration file {} not found'
    
    def __init__(self, config_path=SILO_CONF, rel_path=SILO_REL):
        """
        Allow the caller to specify pathnames that are not standard.  Helps with testing.
        """
        self._config_path = config_path
        self._rel_path = rel_path
        super(EM7Context, self).__init__()
        
    def _populate(self):
        items = self._items
        silo = ConfigParser()
        files_read = silo.read(self._config_path)
        if not files_read:
            raise Em7ConfigurationError(self._err_config_not_found())

        local_attrs = [IPADDR, DBDIR, DBUSER, DBPASS, TYPE]        
        for attr in local_attrs:
            items[attr] = silo.get(LOCAL, attr)
            
        with open(self._rel_path) as f:
            line = f.readline()
            items[BASE_VERSION] = line.strip()

    def _err_config_not_found(self):
        return 'configuration file {} not found'.format(self._config_path)

class EM7NodeManager(manager.NodeManager):
    def _get_app_context(self):
        self._app_ctxt = EM7Context()