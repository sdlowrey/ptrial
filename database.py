"""
Database management for load testing.
"""
import getpass
import MySQLdb

class Database(object):
    """
    Manage MySQL connections and set up databases and tables.
    
    This class is intended to handle artificial databases and tables used for load testing.
    """
    CREATE_DB = 'create database if not exists {}'
    CREATE_TABLE = 'create table {}'
    DROP_DB = 'drop database {}'
    
    def __init__(self, host, port=3306, user='root', password=''):
        self._db = None
        self._cursor = None
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._session_dbs = []
        self._get_db()
        
    def _get_db(self):
        """Create MySQL Connection and Cursor objects.
        
        TODO: replace password auth with SSL.
        https://dev.mysql.com/doc/refman/5.6/en/ssl-connections.html
        """
        kwargs = { 'host': self._host, 'port': self._port, 
                   'user': self._user, 'passwd': self._password } 
        self._db = MySQLdb.Connection(**kwargs)
        self._cursor = self._db.cursor()
        self._cursor.execute('show databases')
        self._all_dbs = [name[0] for name in self._cursor.fetchall()]

    def create_db(self, name):
        """
        Create a MySQL database.  If the name already exists, return quietly.
        
        The created db will be the default/current database for subsequent operations.
        """
        if name in self._session_dbs:
            return
        create = Database.CREATE_DB.format(name)
        self._cursor.execute(create)
        self._cursor.execute('use {}'.format(name))
        self._session_dbs.append(name)
        
    def create_table(self, table):
        print str(table)
        self._cursor.execute(str(table))
        
    def db_list(self, list_all=False):
        """Get a list of databases created by this module.
        
        Args:
          list_all: get all databases (with respect to user permissions) (boolean)
        """
        if not list_all:
            return self._session_dbs
        else:
            return self._all_dbs
        
    def drop_db(self, name):
        self._cursor.execute(self.DROP_DB.format(name))
        
class Table(object):
    def __init__(self, name):
        self.name = name
        self._columns = []
        self._sql = 'create table {} ('.format(self.name)
        
    def define_column(self, col):
        self._columns.append(str(col))
        
    def __str__(self):
        self._sql += ', '.join(self._columns)
        self._sql += ');'
        return self._sql
        
class Column(object):
    """
    Column definitions a la Django. 
    """
    def __init__(self, name, pk=False):
        self.name = name
        self._is_primary = pk
        self._sql = None

    def __str__(self):
        # hacky -- can only be one PK
        if self._is_primary:
            self._sql += ' key'
        return self._sql

class AutoField(Column):
    """
    Auto-increment integer, always primary key.
    """
    def __init__(self, name):
        super(AutoField, self).__init__(name, pk=True)
        self._sql = '{} int unsigned not null auto_increment'.format(name) 
        
class CharField(Column):
    def __init__(self, name, max_len, pk=False):
        super(CharField, self).__init__(name, pk)
        self._max_len = max_len
        self._sql = '{} varchar({})'.format(self.name, self._max_len)