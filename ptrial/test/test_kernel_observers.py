"""
Unit test cases for kernel observers
"""
from ptrial.observer.kernel import ProcessQueueObserver, StorageQueueObserver
import util
from Queue import Queue, Empty
from threading import Thread
import time
import unittest

class StorageObserverTest(unittest.TestCase):
    """
    A StorageObserver grabs stats for a storage device for a directory/partition.
    """
    def setUp(self):
        name = 'var partition'
        self.obs = StorageQueueObserver(name)
        self.obs.set_device('/var')
        self.q = Queue()

    def verify(self, data):
        if data is self.obs.end_data:
            return
        now = int(time.time())
        for k in data.keys():
            if k is 'name':
                self.assertEqual(data[k], self.obs.name)
            else:
                self.assertAlmostEqual(k, now)
                for metric in data[k].keys():
                    self.assertIn(metric, self.obs.field_names)
                    self.assertGreaterEqual(data[k][metric], 0)

    def test_iter_2(self):
        arg = { 'outq': self.q, 'count': 2 }
        t = Thread(target=self.obs.run, kwargs=arg)
        t.start()
        data = {}
        while data is not self.obs.end_data:
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
        self.obs = ProcessQueueObserver(name, pid)
        self.q = Queue()

    def test_1_second_iter(self):
        arg = { 'outq' : self.q, 'count': 5 }
        t = Thread(target=self.obs.run, kwargs=arg)
        t.start()
        data = {}
        while data is not self.obs.end_data:
            data = self.q.get(timeout=2)
            print data
        self.obs.stop()
        t.join()
