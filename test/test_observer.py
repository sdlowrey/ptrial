# Max line length = 100                                                                            1
#        1         2         3         4         5         6         7         8         9         0
#234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
#
# Use the 'runtest' command from the top-level directory.

import json
import observer
from Queue import Queue
from threading import Thread
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
        self.assertRaises(TypeError, observer.ObserverBase)

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
        obs = observer.ObserverBase('dummy', time_format=observer.OBS_ASCII_TIME)
        obs.get_datapoint()
        # just check the decade by looking at the first 3 characters of the key
        decade = int(obs._datapoint.keys()[0][:3])
        self.assertEqual(decade, 201)


class LoopObserverTestCase(unittest.TestCase):
    """
    Test a continuous loop observer, which runs in its own thread and communicates with other
    threads via queue.
    """        
        
    def test_interval_data(self):
        input_q = Queue()
        obs = observer.LoopObserver('looper')
        obs_thread = Thread(target=obs.run, args=(input_q,))
        obs_thread.start()

        for i in range(3):
            data = input_q.get(timeout=2)
            self.assertAlmostEqual(data.keys()[0], int(time.time()))
            self.assertEqual(data.values()[0], {'test': None})
            time.sleep(1)
        obs.stop()
        obs_thread.join()
