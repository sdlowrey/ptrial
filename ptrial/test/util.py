import  os

def pids_by_name(search_str):
    """Search all process command lines for a string.
    
    Returns:
      List of matching (integer) process identifiers 
    """
    pids = []
    for p in [pid for pid in os.listdir('/proc') if pid.isdigit()]:
        with open('/proc/{}/cmdline'.format(p)) as f:
            cmd = f.readline()
        if search_str in cmd:
            pids.append(int(p))
    return pids
