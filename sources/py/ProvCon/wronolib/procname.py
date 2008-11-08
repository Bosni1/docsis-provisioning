__all__ = [ "set_process_name" ]
from dl import open as dlopen

_libc = dlopen ("/lib/libc.so.6")

def set_process_name (  name ):
  _libc.call ( "prctl", 15, name, 0, 0)

  