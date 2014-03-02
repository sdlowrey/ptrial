import unittest
import observer

class BaseObserverTestCase(unittest.TestCase):
    def setUp(self):
        self.obs = observer.ObserverBase()
    
    def test_simple(self):
        """
        Test the test.
        """
        self.assertIsNone(self.obs._source)
        