#!/bin/env python
import ProvCon
from multiprocessing import Process
from threading import Thread
import Queue as ThreadingQueue

from multiprocessing.connection import Listener, Client
import select, os, sys
import ui

class CLIWorker(Thread):
    def __init__(self, queue, logger):
        Thread.__init__(self, None, None, "pcUIw")
        self.queue = queue
        self.logger = logger
        self.start()
    
    def run(self):        
        ProvCon.set_process_name ( "0@@UI_JOB" )
        while True:
            msg, cnx = self.queue.get()               
            if msg is None: break
            result = None
            try:
                self.logger ( `msg` )            
                result = ui.action ( msg['path'], None, **msg['args'] )
            except ui.uierror as err:
                self.logger ( "Failure! %s" % str(err) )
                cnx.send ( { 'result' : None, 'error' : str(err)} )
            except:
                info = sys.exc_info()[:2]
                self.logger ( "Error: [%s, %s]" % (info[0], info[1]) )
                
            try:
                cnx.send ( {'result' : result} )
            except:
                self.logger ( "Error in send!" )
                pass
                                
class CLIServer (Listener):
    def __init__ (self):
        config = ProvCon.Configuration()
        self.logger = ProvCon.LoggingClient(name="UIHUB")
        addr = ProvCon.parse_socket_address ( config.get ( "CLI", "server_address" ) )
        try: os.unlink (addr)
        except: pass
        self.logger( "Starting. Listening on {0}".format (addr) )
        Listener.__init__(self, addr)
        self.queue = ThreadingQueue.Queue(1024)
        self.workers = [CLIWorker(self.queue, self.logger) for i in range(0,5)]
        
    def serve(self):
        self.on = True
        #This is rather bad. There is no guarantee that these fields will be kept in
        #the future versions. Also there is no guarantee that _listener, has a _socket
        #since it may be a Windows named pipe. Bu we'll worry about that when we start
        #porting to Win32, which will probably be never.
        serverfd = self._listener._socket.fileno()        
        poller = select.poll()
        poller.register ( serverfd, select.POLLIN | select.POLLPRI )
        connection_map = {}
        running = True
        
        while running:
            ready = poller.poll ( 30000 )
            for fd, event in ready:
                self.logger ( "({0}, {1})".format (fd, event) )
                if fd == serverfd:
                    self.logger ( "New connection %d %d" % (fd, event) )
                    cnx = self.accept()
                    connection_map [cnx.fileno()] = cnx
                    cnx.send ( ui.signature() )
                    poller.register ( cnx.fileno(), select.POLLIN | select.POLLPRI )
                else:
                    cnx = connection_map.get ( fd, None )
                    if cnx is None:
                        self.logger ( "Error: fd is not in connection map." )
                        continue
                    try:
                        msg = cnx.recv()                               
                        if msg == "_SHUTDOWN": 
                            running = False
                            cnx.close()
                            break
                        self.queue.put ( (msg, cnx) )
                    except EOFError:
                        self.logger ( "Connection({0}) closed.".format (fd))
                        del connection_map[fd]
                        poller.unregister(fd)
                        cnx.close()
                        continue
                    except IOError:
                        info = sys.exc_info()[:2]
                        self.logger ( "Error: %s, %s." % ( info[0], info[1] ) )
                        del connection_map[fd]
                        poller.unregister(fd)
                        cnx.close()
                        continue
                                      
            self.logger("POLL INT")
        self.logger ( "JOIN" )
        for w in self.workers: self.queue.put ( (None, None) ) 
        for w in self.workers: w.join()
        
        
def CLIClient ():
    config = ProvCon.Configuration()
    addr = ProvCon.parse_socket_address ( config.get ( "CLI", "server_address" ) )
    return Client (addr)
        
    
    
    
            