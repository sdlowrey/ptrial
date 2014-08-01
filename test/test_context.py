"""
Tests for core context classes.
"""
import unittest
from ptrial.context.core import OperatingSystemContext, HardwareContext
from ptrial.context.core import HOSTNAME, CPU_FILE, CPU_MODEL, CPU_NCORES

TEST_CPUINFO = 'cpuinfo'
TEST_NCORES = 6
TEST_MODEL = 'Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.10GHz'


class OsContextTestCase(unittest.TestCase):
    """
    Test OS configuration retrieval.
    """

    def setUp(self):
        self.os = OperatingSystemContext()
        
    def test_hostname(self):
        """
        Assert hostname can be accessed with "map style" or "attribute style".  Ensure that it is a 
        string with length > 0.
        """
        hostname = self.os[HOSTNAME]
        self.assertIsInstance(hostname, str)
        self.assertGreater(len(hostname), 0)
        self.assertEqual(hostname, self.os.hostname)
        
        
class HardwareContextTestCase(unittest.TestCase):
    """
    Test hardware configuration retrieval.
    """
    def setUp(self):
        self.hw = HardwareContext(TEST_CPUINFO)
        
    def test_cpu(self):
        ncores = self.hw[CPU_NCORES]
        model = self.hw[CPU_MODEL]
        self.assertEqual(ncores, TEST_NCORES)
        self.assertEqual(model, TEST_MODEL)
    