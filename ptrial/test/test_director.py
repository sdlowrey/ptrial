"""
Tests for the Director classes.

Use the 'runtest' command from the top-level directory.
"""
import director
import unittest
import util

TESTER = 'John Smith'
DESCR = 'Description of the trial'
EMAIL = 'jsmith@funmail.org'

class DirectorInitTest(unittest.TestCase):
    """
    Create Director and verify context.
    """
    def setUp(self):
        self.nm = director.Director(TESTER, DESCR, EMAIL)
        
    def test_director_ctxt(self):
        pass
