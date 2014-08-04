"""
Test for the base classes in the observer.core module
"""
from ptrial.observer.core import (ObserverBase, ObserverError, LoopObserver,
                                   TestObserver, TestLoopObserver)
from ptrial.observer.core import ASCII_TIME
from Queue import Queue, Empty
from threading import Thread
import time
import unittest

Q_TIMEOUT = 2

class BaseObserverNameTestCase(unittest.TestCase):
    """
    Verify Observer naming.
    """
    def test_good_name(self):
        name = 'test observer'
        obs = ObserverBase(name)
        self.assertEqual(obs.name, name)
        del obs

    def test_no_name(self):
        self.assertRaises(TypeError, ObserverBase)

    def test_empty_name(self):
        name = ''
        self.assertRaises(ObserverError, ObserverBase, name)

    def test_numeric_name(self):
        name = 1234
        obs = ObserverBase(name)
        self.assertEqual(obs.name, '1234')

class ObserverDataTestCase(unittest.TestCase):
    """
    The TestObserver can return a test datapoint.  The timestamp is now and the data is a
    dict with a single test element.  

    The TestLoopServer observer continually returns test data.
    """

    def setUp(self):
        self.metric_name = 'test'
        self.observer_name = 'testlooper'
        self.datarange = range(1,999999)

    def verify(self, data):
        """
        Check a test data dictionary.  Walk through all the keys (timestamps) and then verify the
        value (metrics) by walking through each of those keys.
        """
        now = int(time.time())
        for k in data.keys():
            if k is 'name':
                self.assertEqual(data[k], self.observer_name)
            else:
                self.assertAlmostEqual(k, now)
                for metric in data[k].keys():
                    self.assertEqual(metric, self.metric_name)
                    self.assertIn(data[k][metric], self.datarange)

    def test_ascii_time_format(self):
        obs = TestObserver('dummy', time_format=ASCII_TIME)
        obs.get_datapoint()
        # delete the 'name' attribute, leaving only the timestamp key/value
        # just check the decade by looking at the first 3 characters of the key
        del obs._datapoint['name']
        decade = int(obs._datapoint.keys()[0][:3])
        self.assertEqual(decade, 201)

    def test_interval_data_count(self):
        """
        Test LoopObserver using a count limit.
        """
        input_q = Queue()
        obs = TestLoopObserver(self.observer_name, input_q, count=3)
        obs_thread = Thread(target=obs.run)
        obs_thread.start()
        while True:
            data = input_q.get(timeout=Q_TIMEOUT)
            if data is obs.end_data:
                break
            self.verify(data)
        obs.stop()
        obs_thread.join()

    def test_interval_data_stop(self):
        """
        Test loop observer with explicit stop.  
        """
        input_q = Queue()
        obs = TestLoopObserver(self.observer_name, input_q)
        obs_thread = Thread(target=obs.run)
        obs_thread.start()
        time.sleep(3)  # queue up some data
        obs.stop()
        obs_thread.join()

    def test_one_shot(self):
        """
        Test a single datapoint fetch with default integer time -- no queues.
        """
        obs = TestObserver('utest')
        dp = obs.get_datapoint()
        # stupid test but its a simple sanity check
        self.assertEqual(dp['name'], 'utest')
        
    def test_timestamp_as_value(self):
        obs = TestObserver('ts_test', time_as_key=False)
        dp = obs.get_datapoint()
        # stupid test but its a simple sanity check
        self.assertIn('time', dp)
        self.assertIsInstance(dp['time'], int)
