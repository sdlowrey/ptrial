import observer
import os
import recorder
import tempfile
import unittest

class FileRecorderTest(unittest.TestCase):
    def setUp(self):
        self.obs = observer.TestObserver('test observer', data_format=observer.CSV_DATA)
        self.tmpfile = tempfile.NamedTemporaryFile(prefix='rec_', delete=False)
        self.header = ','.join(self.obs.field_names)
        self.rec = recorder.TextFile(self.tmpfile, header=self.header)
        
    def test_single_write(self):
        """
        Get a single fake datapoint, write it, then read it.  Verify that a header line was
        written and then the data."""
        dp = self.obs.get_datapoint()
        self.rec.store(dp)
        # oh, the crap we have to do for unit testing file output (reading while file is open)
        self.tmpfile.flush()
        os.fsync(self.tmpfile)
        
        with  open(self.tmpfile.name, 'r') as f:
            l = f.readlines()
        # verify the header line first
        self.assertEqual(l[0].strip(), self.header)
        # convert everything to int since we know the structure of the test datapoint
        ts, val1, val2 = map(int, l[1].strip().split(','))
        self.assertEqual(val1, self.obs.datapoint[ts]['thing1'])
        self.assertEqual(val2, self.obs.datapoint[ts]['thing2'])
        
    def tearDown(self):
        os.remove(self.tmpfile.name)