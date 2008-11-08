#!/bin/env python
from log import LoggingServer, LoggingClient
from cli import CLIServer, CLIClient
from TFTP import pcTFTPD as TFTPD
from ProvCon.wronolib import set_process_name

ConfigFile = "/Provisioning/etc/ProvCon.cfg"
ControllerKey = "VERY_VERY_QUIET"

def PreLaunchCheck():
    pass

def Controller ( path ):
    from multiprocessing.connection import Listener
    from os import unlink
    #config = Configuration()
    try: unlink (path)
    except: pass
    
    return Listener ( path, authkey=ControllerKey )

def ControllerWait ( ctrl ):
    connection = ctrl.accept ()
    msg = connection.recv()
    connection.close()
    return msg

def ControllerAction (path, action):
    from multiprocessing.connection import Client
    c = Client ( path, authkey = ControllerKey )
    c.send ( action )
    c.close()    

def Configuration():
    from ConfigParser import ConfigParser
    cfg = ConfigParser()
    cfg.read ( ConfigFile )
    return cfg

def ConfigurationChecksum():
    import md5
    h = md5.md5()
    with open(ConfigFile, 'r') as f:
        h.update (f.read())
    return h.hexdigest()

def parse_socket_address (addr):
    if addr.startswith("unix://"):
        return addr[7:]
    elif addr.startswith("udp://"):
        atidx = addr.rfind ( '@' )
        return (addr[6:atidx], int(addr[atidx+1:]))
    elif addr.startswith("tcp://"):
        atidx = addr.rfind ( '@' )
        return (addr[6:atidx], int(addr[atidx+1:]))
    else:
        return addr
        