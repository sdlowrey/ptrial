import em7_config
import unittest

CONFIG = 'silo-test.conf'
RELEASE = 'em7-release'

TEST_IP =  '10.0.12.8'
TEST_APPLIANCE_TYPE = '2'
TEST_VERSION = 'EM7_G3 7.3.6.5 [build 30297]'

class TestEm7Configuration(unittest.TestCase):
    def setUp(self):
        self.em7 = em7_config.Em7Configuration(CONFIG, RELEASE)
        
    def test_basic(self):
        em7 = self.em7
        self.assertEqual(em7[em7_config.IPADDR], TEST_IP)
        self.assertEqual(em7[em7_config.TYPE], TEST_APPLIANCE_TYPE)
        self.assertEqual(em7[em7_config.BASE_VERSION], TEST_VERSION)
