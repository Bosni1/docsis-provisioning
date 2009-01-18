#!/bin/env python
##$Id$
from multiprocessing import Process
from multiprocessing.connection import Listener, Client
import time, sys

import ProvCon
from app import APP

class Provisioning:
    _services_ = [
        ("tftpd", APP.Services.TFTP),
        ]
    _shutdown_sequence_ = [
        "tftpd",
        ]
        
    def run(self):
        
        self.logging_server = APP.LoggingServer()
        self.logger = APP.LoggingClient(name="MAIN")
        logger = self.logger
                
        logger( "-=<" + ("-" * 70) + ">=-" )
        logger("Provisioning v0.01, started." )

        self.controllers = {}
        for (cname, cpath) in APP.BE.CONTROLLER: self.controllers[cname] = cpath

        self.processes = {}
        self.start_services()
        self.cli = APP.CLIServer()
        self.cli.serve()
        self.exit()
        
    def start_services(self):
        for (service, srvclass) in self._services_:
            self.logger("Starting %s." % service)
            self.processes[service] = srvclass()

    def stop_services(self):
        for service in self._shutdown_sequence_:
            self.logger("Stopping %s." % service)
            APP.ControllerAction ( self.controllers[service], "STOP" )
            self.processes[service].join()
            
    def exit(self):
        self.logger("Starting shutdown.")
        self.stop_services()
        self.logger ("Goodbye.")
        self.logger( "-=<" + ("-" * 70) + ">=-" )
        self.logger.shutdown_logger()
        self.logging_server.join()

def UnhandledExceptionHook(extype, exvalue, tb):
    import traceback
    print "*" * 80
    print "EXCEPTION: %s" % extype.__name__
    print "Stack trace:"
    for filename,line,func,code in traceback.extract_tb (tb):
        print "+ File %s in %s:\n\t[line%4d] %s" % (filename, func, line, code)
    print "ERROR: %s" % exvalue
    print "*" * 80

sys.excepthook = UnhandledExceptionHook    
        

print "Hello! I am Provisioning v1.0 and I will be running as a daemon!"
APP.Functions.daemonize ('/dev/null', APP.BE.LOGGING.stdout, APP.BE.LOGGING.stdout )
APP.Functions.set_process_name ( "0@@Provisioning" )
p = Provisioning()

try:
    p.run()
except:    
    UnhandledExceptionHook ( *sys.exc_info() )
    p.exit()
    
