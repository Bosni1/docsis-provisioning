#!/bin/env python
from multiprocessing import Process, Queue
from multiprocessing.connection import Client
from Queue import Queue as ThreadingQueue

import os, time, signal, sys

import ProvCon
from ProvCon.wronolib.procname import set_process_name
import Server, Protocol

"""
The provisioning TFTP server is a multitasking application which
not only serves file contents via TFTP, but also ensures that
sent files are up to date with the provisioning database.

The main process should create an instance of TFTPProvisioningServer
and run the serve_forever method.
The server starts the following processes:
 - TFTPDataSenders which communicate with clients,
 - File "cooks", which check permisions and update the requested files,
Each "cook" is provided with an "oven" - an object that does the actual
preparation and updating of files.

TFTPDataSender : Process
The TFTPProvisioningServer starts a conigured number o these processes. Their
purpose is to wait or items to become available on the "Ready Files Queue"
then connect to the client and send the file contents.
"""
class TFTPDataSender(Process):       
    def __init__(self, rfQueue):
        Process.__init__(self, None, None, "pcTFTP_DATA")
        self.rfQueue = rfQueue
    
    #The loop stops until a "None" is the first element of
    #the tuple read from the queue
    def run(self):
        set_process_name ( "0@TFTPD_DATA" )
        logger = ProvCon.LoggingClient ( name = "TFTPD%05d" % self.pid )
        queue_errors = 0
        while 1:
            try:
                (client_address, initiating_packet, filename, filesize) = self.rfQueue.get()
            except:
                queue_errors += 1
                if queue_errors > 2:
                    logger ("Too many errors reading rfqueue")
                    break
                time.sleep(queue_errors)
            
            queue_errors = 0
            if client_address is None: break
            logger ("Sending %s to %s" % (filename, client_address))
            try:
                with open(filename, 'r') as source:
                    try:
                        (bytes, dt, speed) = Protocol.Handle_RRQ (initiating_packet, client_address, source)
                        logger ( "Sent %d bytes to %s at %.1f kB/s" % (bytes, client_address, speed/ 1024) )
                    except Protocol.TFTPProtocolError as e:
                        logger ( "TFTP Protocol Error: %s" %  e )
            except:
                info = sys.exc_info()[:2]
                logger ( "TFTP error: %s, %s" % (info[0], info[1]))                

        logger ( "EXIT" )
 
class CableModemConfigCook(Process):
    def __init__(self, myQueue, rfQueue, oven):
        Process.__init__(self, None, None, "pcCMCFG_COOK")
        self.myQueue = myQueue
        self.rfQueue = rfQueue
        self.oven = oven
    
    def run(self):
        set_process_name ( "0@TFTPD_CMCFG" )
        pass
        
class FileCook(Process):
    def __init__(self, myQueue, rfQueue, fileOven):
        Process.__init__(self, None, None, "pcTFTP_COOK")
        self.myQueue = myQueue
        self.rfQueue = rfQueue
        self.oven = fileOven
        
    def run(self):
        set_process_name ( "0@TFTPD_FILE" )
        logger = ProvCon.LoggingClient ( name="TFTP_FILE" )
        while True:
            (initiating_packet, client_address) = self.myQueue.get()
            if initiating_packet is None: break
            print "cooking %s" % initiating_packet
            (filename, filesize) = self.oven.prepare (initiating_packet.filename, client_address[0])
            if filesize < 0:
                logger ( "%s, ERROR, %s" % (client_address[0], filename) )
                Protocol.Send_ERROR (client_address, 0, filename)
            else:
                try:
                    self.rfQueue.put ( (client_address, initiating_packet, filename, filesize) )
                except ThreadingQueue.full:
                    logger ( "%s, ERROR, rf queue full" % (client_address[0],) )
                    Protocol.Send_ERROR (client_address, 0, 'rf queue full' )

#An "oven" is an object that prepares files to be sent to clients.
#An oven operates in a specified directory, and limits the files
#served to the ones matching a specified umask.
#The ovens also support a simple permisions mechanism - there are two
#lists of access controls - denylist and allowlist, all requests matching an
#entry in the allowlist are ... allowed, ones matching the denylist are
#rejected. The order in which these lists are processed is defined by the
#'order' field.
#The format of the access controls is (type_of_acl, value).
#There are 2 types of acl suported - filename and ip:
#  e.g.   ( 'file', 'cm-.*\.cfg' )
#         ( 'ip', '10.1.0.0/16' )
#         ( 'file', 'cm-%(IP)s\.cfg' )  (the pattern uses the client ip address)
#         ( 0, 0)                    match everything
class BaseOven:
    def __init__(self, **kkw):
        self.root = os.path.abspath(os.path.dirname(kkw['root']))
        self.umask = kkw.get('umask', 0644 )
        self.denylist = []
        self.allowlist = []
        self.order = kkw.get ('order', "allow")
        self.name = kkw.get ('name', str(self.__class__))
    
    def deny (self, expression):
        (expr_type, expr) = expression
        self.denylist.append ( expression )

    def allow (self, expression):
        (expr_type, expr) = expression
        self.allowlist.append ( expression )
    
    def check_access_list (self, filename, remote_address, acl):
        for (aclt, aclv) in acl:
            if aclt == 0: return True
        return False


    def check_access (self, filename, remote_address):
        if self.order == "allow":
            if self.check_access_list(filename, remote_address, self.allowlist):
                return True
            elif self.check_access_list(filename, remote_address, self.denylist):
                return False
            return True
        elif self.order == "deny":
            if self.check_access_list(filename, remote_address, self.denylist):
                return False
            elif self.check_access_list(filename, remote_address, self.allowlist):
                return True
            return True
        else:
            return False
        
    def prepare (self, filename, remote_address):
        if self.check_access(filename, remote_address):
            return ("/dev/null", 0)
        else:
            return ("Access denied", -1)
        
    def __repr__(self):
        return "<Oven> %s" % self.name
    
#A simple oven, serving files from its root directory as they are
class FileOven (BaseOven):
        
    def prepare(self, filename, remote_address):        
        if not self.check_access(filename, remote_address): return ("Access denied", -1)
        filename = self.root + "/" + filename        
        print filename        
        filepath = os.path.dirname (filename)
        print filepath
        if filepath != self.root: return ("Access denied (DIR)", -1)
        if not os.path.isfile(filename): return ("ENOEXIST", -1)
        stats = os.stat ( filename )
        if stats.st_mode & self.umask != self.umask:
            return ("Access denied (mode)", -1)
        return (filename, stats.st_size)
                
    
class CableModemConfigOven(BaseOven):
    pass


class ProvisioningTFTPServer(Server.BaseTFTPServer):
    def __init__(self):
        Server.BaseTFTPServer.__init__(self)
        set_process_name ( "0@TFTPD_LISTEN" )
        self.config = ProvCon.Configuration()
        self.logger = ProvCon.LoggingClient ( name="TFTPD_SRV" )
        #The queue for "ready-to-be-sent" files
        self.rfQueue = Queue(2048)
        
        #The base oven & cook - simple TFTP
        base_oven = FileOven ( root = self.config.get ( "TFTP", "dir" ), name="FILES" )
        self.logger ( "Setting up %s." % base_oven )
        base_queue_size =  self.config.getint ("TFTP", "queue_size")
        base_cook_queue = Queue(base_queue_size)
        
        #The cook for cm firmware files
        cm_fw_oven = FileOven ( root = self.config.get ("DOCSIS", "fwdir"), name="CM FW" )
        self.logger ( "Setting up %s." % cm_fw_oven )
        cm_fw_oven.deny ( (0,0) )
        cm_fw_queue = Queue(16)
        
        #The cook for cm config files
        cm_cfg_oven = CableModemConfigOven ( root = self.config.get ("DOCSIS", "dir"), name="CM CONFIG" )
        self.logger ( "Setting up %s." % cm_cfg_oven )        
        cm_cfg_oven.deny ( (0,0) )
        cm_cfg_queue_size = self.config.getint ( "DOCSIS", "tftp_queue_size" )
        cm_cfg_queue = Queue (cm_cfg_queue_size)
        
        #The sub-processes count
        base_cooks_count = self.config.getint ("TFTP", "cooks")
        cm_fw_cooks_count = self.config.getint ("DOCSIS", "tftp_cm_fw_cooks")
        cm_cfg_cooks_count = self.config.getint ("DOCSIS", "tftp_cm_cfg_cooks")        
        
        self.cooks = [ 
            (cm_cfg_oven, cm_cfg_queue, [CableModemConfigCook(cm_cfg_queue, self.rfQueue, cm_cfg_oven) for i in range(0,cm_cfg_cooks_count)]),
            (cm_fw_oven, cm_fw_queue, [FileCook(cm_fw_queue, self.rfQueue, cm_fw_oven) for i in range(0,cm_fw_cooks_count)] ),
            (base_oven, base_cook_queue, [FileCook(base_cook_queue, self.rfQueue, base_oven) for i in range(0,base_cooks_count)]),             
                     ]
        self.logger ( "Starting the cooks." )
        #run cooks, run!
        for (_,_,cooklist) in self.cooks:
            for cook in cooklist: cook.start()
        
        data_senders_count = self.config.getint ( "TFTP", "senders" )
        self.data_senders = [ TFTPDataSender (self.rfQueue)  for i in range(0,data_senders_count) ]
        for sender in self.data_senders: sender.start()
        
        signal.signal ( signal.SIGHUP, self.shutdown )        
        self.on = True
        #self.timeout = 4
        error_count = 0
        while self.on:   
            try:
                self.handle_request()
            except Exception as e:                
                error_count += 1
                self.logger ( "error#%d in handle_request (%s)" % (error_count, e) )
                if error_count > 10: break
        self.logger ( "TFTP service no longer active." )
        
    def handle_RRQ (self, ipacket, client_address):
        for cook in self.cooks:
            (oven,queue,plist) = cook
            if oven.check_access (ipacket.filename, client_address[0]):                    
                try:
                    self.logger ( "RRQ from %s filename=%s" % (client_address[0], ipacket.filename) )
                    queue.put_nowait ( (ipacket, client_address) )
                    return True
                except ThreadingQueue.full:
                    self.logger ( "RRQ from %s FAILED (QUEUE FULL)" % (client_address[0],) )
                    Protocol.Send_ERROR ( client_address, 0, "cook queue full" )
            #else:
            #    print "access denied in oven: ", oven
        return False
    
    def shutdown(self, *kw):        
        self.logger ( "Server shutdown in progress." )        
        for (_,queue,cooks) in self.cooks:                        
            for cook in cooks:                
                queue.put ( (None, None) )
        for sender in self.data_senders:            
            self.rfQueue.put ( (None,None,None,None) )
        for sender in self.data_senders:            
            sender.join()
        for (_,queue,cooks) in self.cooks:            
            for cook in cooks: cook.join()        
        self.on = False
            
class pcTFTPD(Process):
    def __init__(self):
        Process.__init__(self, None, None, "pcTFTPD" )
        self.start()
        
    def run(self):
        set_process_name ( "0@TFTPD" )
        config = ProvCon.Configuration()
        logger = ProvCon.LoggingClient ( name="TFTPD" )
        
        controller = ProvCon.Controller( config.get ( "CONTROLLER", "tftpd") )
        
        logger ( "Initializing the server." )
        server_process = Process ( name="TFTPD_LISTEN", target=ProvisioningTFTPServer )
        server_process.start()
        
        while True:
            action = ProvCon.ControllerWait ( controller )
            if action == "STOP": break
        
        logger ("Terminating the server.")
        os.kill ( server_process.pid, signal.SIGHUP )        
        logger ("Waiting for all children to exit.")                
        server_process.join()
        logger ( "Finished." )
            
#config = ProvCon.Configuration()
#TFTPD = pcTFTPD()
#time.sleep(2)
#ProvCon.ControllerAction ( config.get ( "CONTROLLER", "tftpd"), "STOP" )
#TFTPD.join()