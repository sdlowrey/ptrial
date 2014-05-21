import encoder
import unittest

TIMESTAMP = 1400620976

class EncoderTest(unittest.TestCase):
    
    
    def setUp(self):
        self.data = {'name': 'my test name',  TIMESTAMP: {'metric1': 1231, 'metric2': 989}}
        self._enc = encoder.Encoder()
        
    def test_json(self):    
        self._enc.set_format(encoder.JSON_DATA)
        jdata = self._enc.encode(self.data)
        print jdata
        
    def test_csv(self):
        self._enc.set_format(encoder.CSV_DATA)
        self._enc.set_order(['metric2', 'metric1'])
        cdata = self._enc.encode(self.data)
        met = self.data[TIMESTAMP]
        expected = '{},{},{}'.format(TIMESTAMP, met['metric2'], met['metric1'])
        self.assertEqual(cdata, expected)
