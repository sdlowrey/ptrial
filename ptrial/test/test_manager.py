"""
Tests for the Manager classes.

Use the 'runtest' command from the top-level directory.
"""
import manager
import observer
from Queue import Queue, Empty
from threading import Thread
import time
import unittest
import util


class NodeManagerInitTest(unittest.TestCase):
    """
    Create NodeManager and verify context.
    """
    def setUp(self):
        trial_ctxt = {} # empty context from trial director
        self.nm = manager.NodeManager(trial_ctxt)
        
    def test_hw_ctxt(self):
        pass
    