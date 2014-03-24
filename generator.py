"""
Emulate system load by generating data in files, memory, and databases.

This is just a test bed at the moment...
"""
import MySQLdb
import random
import tempfile

SILO_DB_PORT = 7706

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

def get_db(host, user, password, port=SILO_DB_PORT):
    kwargs = { 'host': host, 'port': port, 'user': user, 'passwd': password } 
    
    conn = MySQLdb.Connection(**kwargs)
    
    return conn

if __name__ == '__main__':
    #print '1 byte to /tmp/{}'.format(randfile('/tmp', 1))
    c = get_db('172.16.10.60', 'root', 'em7admin')
    #test_schema = 'gen_schema_1'
    #create_schema(test_schema)
    c.close()
