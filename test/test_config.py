"""
Test for the ConfigurationBase class and its subclasses.

Use the 'runtest' command from the top-level directory.
"""
TEST_CPUINFO = 'cpuinfo'
TEST_NCORES = 6
TEST_MODEL = 'Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.10GHz'

import config
import unittest

class OsConfigTestCase(unittest.TestCase):
    """
    Test OS configuration retrieval.
    """

    def setUp(self):
        self.os = config.OperatingSystemConfiguration()
        
    def test_hostname(self):
        """
        Assert hostname can be accessed with "map style" or "attribute style".  Ensure that it is a 
        string with length > 0.
        """
        hostname = self.os[config.HOSTNAME]
        self.assertIsInstance(hostname, str)
        self.assertGreater(len(hostname), 0)
        self.assertEqual(hostname, self.os.hostname)
        
        
class HardwareConfigTestCase(unittest.TestCase):
    """
    Test hardware configuration retrieval.
    """
    def setUp(self):
        self.hw = config.HardwareConfiguration(TEST_CPUINFO)
        
    def test_cpu(self):
        ncores = self.hw[config.CPU_NCORES]
        model = self.hw[config.CPU_MODEL]
        self.assertEqual(ncores, TEST_NCORES)
        self.assertEqual(model, TEST_MODEL)
    