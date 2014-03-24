"""
Emulate system load by generating data in files, memory, and databases.

This is just a test bed at the moment...
"""
import getpass
import MySQLdb
import random
import tempfile
import wingdbstub

# notes: change the 50-byte range to a "record size" arg, change nbytes to "nrec"

def randfile(path, nbytes):
    """
    Write random bytes to a file.  A random file name prefixed by "gen_" is created.
    
    Args:
      path: directory to write in
      nbytes: number of bytes to write
      
    Returns:
      name of the file created
    """
    with tempfile.NamedTemporaryFile(prefix='gen_', dir=path, delete=False) as f:
        for i in range(0,nbytes):
            # write 10 bytes
            b = []
            for n in range(0,50):
                b.append(random.randrange(0,256))
            f.write(bytearray(b))
        name = f.name
        f.close()
    return name

class Database(object):
    """
    Class responsible for managing MySQL connections, databases/schemas, and tables.
    
    This class is intended to handle artificial databases and tables used for load testing.
    """
    SILO_DB_PORT = 7706
    GEN_SCHEMA = 'z_{}'
    CREATE_DATABASE = 'create database if not exists {}'
    CREATE_TABLE = 'create table {}'
    
    def __init__(self, host, user, password=None):
        self._db = None
        self._cursor = None
        self._session_schemas = []
        self._get_db(host, user, password)
        
    def _get_db(self, host, user, password, port=SILO_DB_PORT):
        """c
        Create MySQL Connection and Cursor objects.
        
        TODO: replace password auth with SSL.
        https://dev.mysql.com/doc/refman/5.6/en/ssl-connections.html
        """
        if not password: 
            password = getpass.getpass()  # TODO: remove before flight
        kwargs = { 'host': host, 'port': port, 'user': user, 'passwd': password } 
        self._db = MySQLdb.Connection(**kwargs)
        self._cursor = self._db.cursor()

    def create_schema(self, name):
        """
        Create a schema/database.  If the name already exists, return quietly.
        
        The created schema will be the default/current database for subsequent operations.
        """
        if name in self._session_schemas:
            return
        name = Database.GEN_SCHEMA.format(name)
        create = Database.CREATE_DATABASE.format(name)
        self._cursor.execute(create)
        self._cursor.execute('use {}'.format(name))
        self._session_schemas.append(name)
        
    def define_table(self, table):
        print str(table)
        self._cursor.execute(str(table))
        
class Table(object):
    GEN_TABLE = 'gen_{}'
    def __init__(self, name):
        self.name = Table.GEN_TABLE.format(name)
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

if __name__ == '__main__':
    #print '1 byte to /tmp/{}'.format(randfile('/tmp', 1))
    db = Database('172.16.10.60', 'root')
    db.create_schema('testdb')
    t1 = Table('test1')
    t1.define_column(AutoField('id'))
    t1.define_column(CharField('text1', 50))
    db.define_table(t1)