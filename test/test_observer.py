"""
Test for the ObserverBase class and its subclasses.

Use the 'runtest' command from the top-level directory.
"""
import observer
from Queue import Queue, Empty
from threading import Thread
import time
import unittest
import util

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

class ObserverDataTestCase(unittest.TestCase):
    """
    The BaseObserver can "get" a test datapoint.  The timestamp is now and the data is a
    dict with a single test element.  

    The TestLoopServer observer continually returns test data.

    Callers would not normally access the internal datapoint directly, but we can for testing. (The
    data is returned to the caller in a coded format for serialization.)
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
        obs = observer.ObserverBase('dummy', time_format=observer.ASCII_TIME)
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
        obs = observer.TestLoopObserver(self.observer_name)
        args = {'outq': input_q, 'count': 3}
        obs_thread = Thread(target=obs.run, kwargs=args)
        obs_thread.start()
        while True:
            data = input_q.get(timeout=2)
            if data is obs._end_data:
                break
            self.verify(data)
        obs.stop()
        obs_thread.join()

    def test_interval_data_stop(self):
        """
        Test loop observer with explicit stop.  
        """
        input_q = Queue()
        obs = observer.TestLoopObserver(self.observer_name)
        args = {'outq': input_q}
        obs_thread = Thread(target=obs.run, args=(input_q,))
        obs_thread.start()
        time.sleep(3)  # queue up some data
        obs.stop()
        obs_thread.join()

    def test_one_shot(self):
        """
        Test a single datapoint fetch with default integer time -- no queues.
        """
        obs = observer.TestObserver('utest')
        dp = obs.get_datapoint()
        # stupid test but its a simple sanity check
        self.assertEqual(dp['name'], 'utest')
        
class StorageObserverTest(unittest.TestCase):
    """
    A StorageObserver grabs stats for a storage device for a directory/partition.
    """
    def setUp(self):
        name = 'var partition'
        self.obs = observer.StorageObserver(name)
        self.obs.set_device('/var')
        self.q = Queue()

    def verify(self, data):
        if data is self.obs._end_data:
            return
        now = int(time.time())
        for k in data.keys():
            if k is 'name':
                self.assertEqual(data[k], self.obs.name)
            else:
                self.assertAlmostEqual(k, now)
                for metric in data[k].keys():
                    self.assertIn(metric, self.obs.BLOCK_STATS)
                    self.assertGreaterEqual(data[k][metric], 0)

    def test_iter_2(self):
        arg = { 'outq': self.q, 'count': 2 }
        t = Thread(target=self.obs.run, kwargs=arg)
        t.start()
        data = {}
        while data is not self.obs._end_data:
            data = self.q.get(timeout=2)
            self.verify(data)
            print data
        self.obs.stop()
        t.join()

class ProcessObserverTest(unittest.TestCase):
    """
    A ProcessObserver grabs stats for a process as identified by a pid.
    """
    def setUp(self):
        """Get the PID of the first sshd process found."""
        name = 'sshd'
        pid = util.pids_by_name(name)[0]
        self.obs = observer.ProcessObserver(name, pid)
        self.q = Queue()

    def test_1_second_iter(self):
        arg = { 'outq' : self.q, 'count': 5 }
        t = Thread(target=self.obs.run, kwargs=arg)
        t.start()
        data = {}
        while data is not self.obs._end_data:
            data = self.q.get(timeout=2)
            print data
        self.obs.stop()
        t.join()
