import encoder
import unittest

TIMESTAMP = 1400620976

class EncoderTest(unittest.TestCase):
    
    
    def setUp(self):
        self.data = {'name': 'my test name',  TIMESTAMP: {'metric1': 1231, 'metric2': 989}}
        
    def test_json(self):    
        enc = encoder.Encoder(encoder.JSON_DATA)
        jdata = enc.encode(self.data)
        print jdata
        
    def test_csv(self):
        enc = encoder.Encoder(encoder.CSV_DATA, ['metric2', 'metric1'])
        cdata = enc.encode(self.data)
        met = self.data[TIMESTAMP]
        expected = '{},{},{}'.format(TIMESTAMP, met['metric2'], met['metric1'])
        self.assertEqual(cdata, expected)
