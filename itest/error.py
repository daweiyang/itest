'''define SIGErr for SIG response'''
class SIGErr(Exception):
    """SIG catch err"""
    pass

def sighandle(signum, stack_frame):
    raise SIGErr("Terminated by signal %d" % signum)
