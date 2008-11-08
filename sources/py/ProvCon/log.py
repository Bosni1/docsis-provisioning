#!/bin/env python
from multiprocessing import Process, Queue
from multiprocessing.connection import Listener, Client, current_process
import Queue as ThQueue
import time, socket, cPickle
from SocketServer import UDPServer
import ProvCon
import logging, logging.handlers

class LoggingBackend(Process):
    def __init__(self, queue):
        Process.__init__ (self, None, None, "pcLOG_BE")
        self.queue = queue
        
        
    def run(self):        
        ProvCon.set_process_name ( "0@@LOG_BE" )
        config = ProvCon.Configuration ()
        self.logger = logging.getLogger ( "provconf" )
        self.logger.setLevel ( logging.DEBUG )
        self.handler = logging.handlers.RotatingFileHandler ( config.get ( "LOGGING", "filename" ), 
                                                              maxBytes=1024*1024*16, backupCount=8)
        formatter = logging.Formatter ( "%(message)s" )
        self.handler.setFormatter (formatter)        
        self.logger.addHandler (self.handler)
        
        while True:
            (t, source, severity, message) = self.queue.get()            
            if source is None: break 
            self.logger.debug ("[{0}] ({1:14}) {2}".format(
                                   time.strftime("%d-%m-%y %H:%M:%S", time.localtime(t)), 
                                   source[:14], message) )
        

class LoggingServer(Process, UDPServer):

    def __init__ (self):
        config = ProvCon.Configuration()        
        port = config.getint ( "LOGGING", "server_port" )

        UDPServer.__init__(self, ('127.0.0.1', port), None)
        Process.__init__ (self, None, None, "pcLOG" )        
        
        self.queue = Queue( config.getint ( "LOGGING", "queue_size") )        
        self.backend = LoggingBackend (self.queue)
        self.backend.start()
        self.on = True
        self.start()
    
    def finish_request(self, request, client_address):
        ProvCon.set_process_name ( "0@@LOG" )
        data, sock = request
        try:
            (src, svr,msg) = cPickle.loads ( data )                    
            self.queue.put_nowait ( (time.time(), src,svr,msg) )
            if src is None: self.on = False
        except ThQueue.Full:
            print "Full"
        except:
            pass
        
    def run(self):
        while self.on:
            self.handle_request()        
        self.queue.put ( (None, None, None, None) )
        

class LoggingClient:
    def __init__ (self, **kkw):
        config = ProvCon.Configuration()
        self.socket = socket.socket (socket.AF_INET, socket.SOCK_DGRAM )
        port = config.getint ( "LOGGING", "server_port" )
        self.socket.connect ( ('127.0.0.1', port) )
        self.source = kkw.get ( "name", current_process().name )        
        self.level = kkw.get ( "level", 0 )
    
    def log (self, msg, severity=0):
        if severity < self.level: return
        msg = cPickle.dumps ( (self.source, severity, msg) )        
        self.socket.send ( msg )

    def shutdown_logger(self):
        msg = cPickle.dumps ( (None, None, None) )        
        self.socket.send ( msg )
        
    def __call__(self, msg, severity=0):
        return self.log (msg, severity)
    
#srv = LoggingServer()
#c = LoggingClient ()

#for i in xrange(0,500):
    #c ( "TEST %d" % i, 0 )    

#time.sleep(1)
#c.shutdown_logger()
#srv.backend.join()
#srv.join()
