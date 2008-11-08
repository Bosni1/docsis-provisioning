#!/bin/env python

import socket, time
from SocketServer import UDPServer
import Protocol

class BaseTFTPServer (UDPServer):
    allow_reuse_address = 1
    
    def __init__(self, local_address = ('127.0.0.1', 69) ):
        UDPServer.__init__(self, local_address, None)

    def handle_RRQ (self, ipacket, client_address):
        Protocol.Send_ERROR (client_address, 0, "Function not available.")
        return True
    def handle_WRQ (self, ipacket, client_address):
        Protocol.Send_ERROR (client_address, 0, "Function not available.")
        return True
    
    def finish_request(self, request, client_address):
        data, _ = request
        ipacket = Protocol.Packet ( data )
        if ipacket.opcode == Protocol.Packet.RRQ:
            if not self.handle_RRQ (ipacket, client_address):
                Protocol.Send_ERROR (client_address, 2)
        elif ipacket.opcode == Protocol.Packet.WRQ:
            self.handle_WRQ (ipacket, client_address)
        else:
            self.report_error ( "Message from %s, opcode %s, does not belong to a known session." %
                                (client_address, ipacket.opcode) )
    def report_error (self, errmsg):
        print (errmsg)
    

class SimpleTFTPServer (BaseTFTPServer):
    
    def handle_RRQ (self, ipacket, client_address):
        from os import urandom
        from random import randint
        from StringIO import StringIO
        
        print "Handling %s from %s, sending random data." % (ipacket, client_address)
        stream = StringIO ( urandom ( randint(1000,20000) ) )
        Protocol.Handle_RRQ ( ipacket, client_address, stream )
        
        return stream.len()

if __name__ == "__main__":
    TFTP = SimpleTFTPServer()
    TFTP.handle_request()

    