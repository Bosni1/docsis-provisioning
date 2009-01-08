#!/bin/env python

#from log import LoggingServer, LoggingClient
#from cli import CLIServer, CLIClient
#from wronolib import set_process_name
#from ProvCon.wronolib import set_process_name

from os import getenv

ConfigFileBE = (getenv("PROVISIONING_ROOT") or "/home/kuba/src/docsis-provisioning/site") + "/etc/ProvisioningBE.cfg"
"""Path of the configuration file used by the back-end process"""
ConfigFileFE =  (getenv("PROVISIONING_ROOT") or "/home/kuba/src/docsis-provisioning/site") + "/etc/ProvisioningFE.cfg"
"""Path of the configuration file used by front-end processes"""

ControllerKey = "VERY_VERY_QUIET"
"""A shared "secret" used to encrypt Controller communication"""

def PreLaunchCheck():
    pass

def Controller ( path ):
    """
    Create and return a new "Controller" socket.
    
    A "Controller" is a process which listens for remote management requests to the Provisioning
    back-end services (such as TFTPD)

    @type   path: string
    @param  path: path of the unix socket
    
    @rtype:       multiprocessing.connection.Listener
    @return:      the new Listener object
    
    """
    from multiprocessing.connection import Listener
    from os import unlink
    try: unlink (path)
    except: pass
    
    return Listener ( path, authkey=ControllerKey )

def ControllerWait ( ctrl ):
    """
    Wait for a controller request.
    
    @type  ctrl: multiprocessing.connection.Listener
    @param ctrl: a controller created with a call to Controller()
    
    @rtype:      object
    @return:     the message (python object) sent by the client
    """
    connection = ctrl.accept ()
    msg = connection.recv()
    connection.close()
    return msg

def ControllerAction (path, action):
    """
    Send a message to the Controller.
    
    This function is used by remote-management applications to control provisioning services.
    
    @type   path: string
    @param  path: path of the controller socket
    
    @type  action: object
    @param action: the message to send to the controller        
    """
    from multiprocessing.connection import Client
    c = Client ( path, authkey = ControllerKey )
    c.send ( action )
    c.close()    

def Configuration():
    from ConfigParser import ConfigParser
    cfg = ConfigParser()
    cfg.read ( ConfigFileBE )
    return cfg

def ConfigurationFE():
    from ConfigParser import ConfigParser
    cfg = ConfigParser()
    cfg.read ( ConfigFileFE )
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
        