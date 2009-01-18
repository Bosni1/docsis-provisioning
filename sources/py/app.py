from ConfigParser import ConfigParser        
from os import getenv
from exceptions import BaseException

__all__ = [ "APP" ]

_PROVISIONING_ROOT = getenv ("PROVISIONING_ROOT") or "/home/kuba/src/docsis-provisioning/site"
_PROVISIONING_MODE = getenv ("PROVISIONING_MODE") or "DEVEL"

from ProvCon.func.objects import AttrDict

class SectionProxy(object):
    
    def __init__(self, config, sectionname):
        self._configobj = config
        self._sectionname = sectionname        
        
    def __getattr__(self, attrname):  
        try:
            return self.__dict__[attrname]
        except KeyError:
            conv = str
            
            if attrname.startswith ("_i_"):
                attrname = attrname[3:]
                conv = int
            
            if self._configobj._config_parser.has_option (self._sectionname, attrname):
                print attrname, conv
                return conv(self._configobj._config_parser.get (self._sectionname, attrname))
            else:
                raise AttributeError (attrname)          

    def __iter__(self):
        return iter(self._configobj._config_parser.items(self._sectionname))
                    
    def __repr__(self):
        return "CONFIG SECTION [" + self._sectionname + "]"
    
class ProvConConfig(object):
    class ConfigurationError(BaseException):
        def __init__(self, *args):
            BaseException.__init__(self, *args)
            
    def files(self):
        if 0: yield None
        raise StopIteration
        
    def getSectionProxy(self, sectionname):
        if self._config_parser.has_section (sectionname):
            if sectionname not in self._sectionproxies:
                self._sectionproxies[sectionname] = SectionProxy (self, sectionname)
            return self._sectionproxies[sectionname]
        else:
            raise AttributeError
        
    def __init__(self):
        #self.__dict__["__sectionproxies"] = None
        #self.__dict__["__config_parser"] = None
        self._sectionproxies = {}
        self._config_parser = ConfigParser()
        parserOk = False
        for filename in self.files():
            try:                
                self._config_parser.read ( filename )
                parserOk = True
                print self.__class__.__name__, "read " + filename
                break
            except IOError:
                continue
        if not parserOk:
            raise ProvConConfig.ConfigurationError(self.__class__.__name__ + " config file not found." )
        
    def __getattr__(self, attrname):
        if attrname in self.__dict__:
            return self.__dict__[attrname]
        elif self._config_parser.has_section ( attrname ):
            return self.getSectionProxy ( attrname )
            
class App(object):
    
    class Obj_FE(ProvConConfig):        
        def files(self):
            _files = [
                _PROVISIONING_ROOT + "/etc/ProvisioningFE.cfg",
                ]
            for f in _files: 
                yield f

        def __init__(self):
            ProvConConfig.__init__(self)
        
    class Obj_BE(ProvConConfig):
        def files(self):
            _files = [
                _PROVISIONING_ROOT + "/etc/ProvisioningBE.cfg",
                ]
            for f in _files: 
                yield f

        def __init__(self):
            ProvConConfig.__init__(self)
             
    def __getattr__(self, attrname):
        if attrname in self.__dict__:
            return self.__dict__[attrname]
        elif hasattr(self.__class__, "Obj_" + attrname):
            print "Delayed construction of " + attrname
            obj = getattr(self.__class__, "Obj_" + attrname) ()
            self.__dict__[attrname]  = obj
            return obj
        else:
            raise AttributeError
    
    
    def __init__(self):
        from ProvCon.log import LoggingClient, LoggingServer
        from ProvCon.cli import CLIServer, CLIClient
        from ProvCon import ControllerAction, Controller, ControllerWait
        
        self.LoggingClient = LoggingClient
        self.LoggingServer = LoggingServer
        self.CLIServer = CLIServer
        self.CLIClient = CLIClient
        self.ControllerAction = ControllerAction
        self.Controller = Controller
        self.ControllerWait = ControllerWait
        
        self.Services = AttrDict()
        from ProvCon.TFTP import pcTFTPD 
        self.Services.TFTP = pcTFTPD
        
        self.Functions = AttrDict()
        from ProvCon.wronolib import daemonize, set_process_name
        from ProvCon import parse_socket_address
        self.Functions.daemonize = daemonize
        self.Functions.set_process_name = set_process_name
        self.Functions.parse_socket_address = parse_socket_address
        
        
        
        
            
APP = App()