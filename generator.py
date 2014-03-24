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
    GEN_SCHEMA = 'z_schema_{}'
    CREATE_DATABASE = 'CREATE DATABASE {}'
    
    def __init__(self, host, user, password=None):
        self._db = None
        self._cursor = None
        self._session_schemas = []
        self._get_db(host, user, password)
        
    def _get_db(self, host, user, password, port=SILO_DB_PORT):
        """
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
        """
        if name in self._session_schemas:
            return
        name = Database.GEN_SCHEMA.format(name)
        create = Database.CREATE_DATABASE.format(name)
        self._cursor.execute(create)
        self._session_schemas.append(name)
        
if __name__ == '__main__':
    #print '1 byte to /tmp/{}'.format(randfile('/tmp', 1))
    db = Database('172.16.10.60', 'root')
    db.create_schema(1)
