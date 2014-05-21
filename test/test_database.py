"""
test the Database module.  

Note that the terms "database", "Db", etc are used in the MySQL sense, EXCEPT for the module
itself.  The module Database encompasses a MySQL server connection as well as databases, tables, 
etc.
"""
from database import Database
import unittest


class DbCreateDeleteTest(unittest.TestCase):
    def setUp(self):
        self.db = Database('localhost')
        self.dbname = 'gendb'
        
    def test_create_db(self):
        self.db.create_db(self.dbname)
        self.assertIn(self.dbname, self.db.db_list())
    
    def test_drop_db(self):
        self.db.drop_db(self.dbname)
        self.assertNotIn(self.dbname, self.db.db_list())
    
#class DatabaseLoadGeneratorTest(unittest.TestCase):
    #def setUp(self):
        #"""Create a database connection.
        #"""
        #self.db = Database('localhost')
        #t1 = Table('test1')
        #t1.define_column(AutoField('id'))
        #t1.define_column(CharField('text1', 50))
        #self.db.define_table(t1)
                
    #def test_create_schema(self);
    #def test_small_write_load(self):
        #"""Create a small schema with ten tables and write 100 records to each one.
        #"""
        #pass