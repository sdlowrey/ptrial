# Max line length = 100                                                                            1
#        1         2         3         4         5         6         7         8         9         0
#234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
#
# Use the 'runtest' command from the top-level directory.

import json
import observer
import time
import unittest

class BaseObserverNameTestCase(unittest.TestCase):
    """
    Verify Observer naming.
    """
    def test_good_name(self):
        name = 'test observer'
        obs = observer.ObserverBase(name)
        self.assertEqual(obs.name, name)
        del obs
        
    def test_no_name(self):
        self.assertRaises(observer.ObserverError, observer.ObserverBase)

    def test_empty_name(self):
        name = ''
        self.assertRaises(observer.ObserverError, observer.ObserverBase, name)
        
    def test_numeric_name(self):
        name = 1234
        obs = observer.ObserverBase(name)
        self.assertEqual(obs.name, '1234')

class BaseObserverDataTestCase(unittest.TestCase):
    """
    The base observer can "get" a null datapoint.  The timestamp is now and the data is a
    dict with a single test element.  
    
    Callers would not normally access the internal datapoint directly, but we can for testing. (The
    data is returned to the caller in a coded format for serialization.)
    """

    def test_dummy_get(self):
        obs = observer.ObserverBase('dummy')
        obs.get_datapoint()
        self.assertAlmostEqual(obs._datapoint.keys()[0], int(time.time()))
        self.assertEqual(obs._datapoint.values()[0], {'test': None})
        
    def test_ascii_time_format(self):
        obs = observer.ObserverBase('dummy', time_format=observer.OBS_TIME_FORMAT_ASCII)
        obs.get_datapoint()
        # just check the decade by looking at the first 3 characters of the key
        decade = int(obs._datapoint.keys()[0][:3])
        self.assertEqual(decade, 201)

    def test_json_integer_time(self):
        """
        Verify that the integer time stamp can withstand JSON encoding.
        
        The timestamp is an integer key in the Python dict, but keys have to be strings in JSON.
        (Values can still be numeric.)
        """
        obs = observer.ObserverBase('dummy')
        jdata = obs.get_datapoint()
        pdata = json.loads(jdata)
        jtime = int(pdata.keys()[0])
        t = time.gmtime(jtime)
        print 'hellweg:', t
        self.assertAlmostEqual(t, time.gmtime())

        