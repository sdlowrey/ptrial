import em7
import unittest

CONFIG = 'silo-test.conf'
RELEASE = 'em7-release'

TEST_IP =  '10.0.12.8'
TEST_APPLIANCE_TYPE = '2'
TEST_VERSION = 'EM7_G3 7.3.6.5 [build 30297]'

class TestEm7Context(unittest.TestCase):
    def setUp(self):
        self.em7_ctxt = em7.EM7Context(CONFIG, RELEASE)
        
    def test_basic(self):
        _em7 = self.em7_ctxt
        self.assertEqual(_em7[em7.IPADDR], TEST_IP)
        self.assertEqual(_em7[em7.TYPE], TEST_APPLIANCE_TYPE)
        self.assertEqual(_em7[em7.BASE_VERSION], TEST_VERSION)
