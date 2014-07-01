"""
Test for the ConfigurationBase class and its subclasses.

Use the 'runtest' command from the top-level directory.
"""
import config
import unittest

class OsConfigTestCase(unittest.TestCase):
    """
    The TestObserver can return a test datapoint.  The timestamp is now and the data is a
    dict with a single test element.  

    The TestLoopServer observer continually returns test data.
    """

    def setUp(self):
        self.os = config.OperatingSystemConfiguration()
        
    def test_hostname(self):
        """
        Assert hostname can be accessed with "map style" or "attribute style"
        
        The hostname itself is only checked as a string with len > 0.
        """
        hostname = self.os['hostname']
        self.assertIsInstance(hostname, str)
        self.assertGreater(len(hostname), 0)
        self.assertEqual(hostname, self.os.hostname)
        