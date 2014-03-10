"""
Emulate system load by generating data in files, memory, and databases.
"""
import random
import tempfile

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

print randfile('/tmp', 1)
    