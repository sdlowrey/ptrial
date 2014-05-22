import encoder
from observer import TestObserver
import os
import recorder
import tempfile
import unittest

class FileRecorderTest(unittest.TestCase):
    def setUp(self):
        f = tempfile.NamedTemporaryFile(prefix='rec_', delete=False)
        self.tmpfile = f.name
        self._enc = encoder.Encoder(fmt=encoder.CSV_DATA, key_order=['thing2', 'thing1'])
        self.rec = recorder.TextFile(f, self._enc)
        self.obs = TestObserver('test observer')
        
    def test_single_write(self):
        dp = self.obs.get_datapoint()
        self.rec.store(dp)
        with open(self.tmpfile, 'r') as f:
            l = f.readline()
        # convert everything to int since we know the structure of the test datapoint
        ts, val1, val2 = map(int, l.split(','))
        self.assertEqual(val1, dp[ts]['thing2'])
        self.assertEqual(val2, dp[ts]['thing1'])
        
    def tearDown(self):
        os.remove(self.tmpfile)