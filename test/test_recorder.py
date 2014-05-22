import encoder
from observer import TestObserver
import os
import recorder
import tempfile
import unittest

class FileRecorderTest(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(prefix='rec_', delete=False)
        self.key_order =  ['thing2', 'thing1']
        self._enc = encoder.Encoder(fmt=encoder.CSV_DATA, key_order=self.key_order)
        self.rec = recorder.TextFile(self.tmpfile, self._enc)
        self.obs = TestObserver('test observer')
        
    def test_single_write(self):
        dp = self.obs.get_datapoint()
        self.rec.store(dp)
        # oh, the crap we have to do for unit testing file output
        self.tmpfile.flush()
        os.fsync(self.tmpfile)
        with  open(self.tmpfile.name, 'r') as f:
            l = f.readlines()
        self.assertEqual(l[0].strip(), ','.join(self.key_order))
        # convert everything to int since we know the structure of the test datapoint
        ts, val1, val2 = map(int, l[1].strip().split(','))
        self.assertEqual(val1, dp[ts]['thing2'])
        self.assertEqual(val2, dp[ts]['thing1'])
        
    def tearDown(self):
        os.remove(self.tmpfile.name)