#!/bin/env python
import struct
import socket
from time import time
from contextlib import contextmanager

class Packet:
    """TFTP.Protocol.Packet
    The Packet class provides encoding and decoding services for
    TFTP packets as defined in RFC1350:
           2 bytes    string   1 byte     string   1 byte
           -----------------------------------------------
    RRQ/  | 01/02 |  filename  |   0  |    mode    |   0  |
    WRQ    -----------------------------------------------
           2 bytes    2 bytes       n bytes
           ---------------------------------
    DATA  | 03    |   blockno  |    data    |
           ---------------------------------
           2 bytes    2 bytes
           --------------------
    ACK   | 04    |   blockno  |
            --------------------
           2 bytes  2 bytes        string        1 byte
           --------------------------------------------
    ERROR | 05    |  errorcode |   errormessage |   0  |
           --------------------------------------------
    
    Two provided methods are: 

    Packet.decode
    Packet.encode

    Packets may be constructed by using the 'decode' method, providing
    keyword arguments to the constructor, or by manually setting
    properties whose names correspond to packet fields as listed above.
    
    examples:
    >>> rrq = Packet(opcode=Packet.RRQ, filename="test.bin", mode="octet")
    >>> err = Packet(opcode=Packet.ERROR, errorcode=0,errormessage="My custom error message.")
    >>> socket.send (rrq.encode())
    """
    #opcodes
    RRQ = 1
    WRQ = 2
    DATA = 3
    ACK = 4
    ERROR = 5
    #standard error messages
    ERRORMESSAGE = { 
        0 : 'Other error.',
        1 : 'File not found.',
        2 : 'Access violation.',
        3 : 'Disk full or allocation exceeded.',
        4 : 'Illegal TFTP operation.',
        5 : 'Unknown transfer ID.',
        6 : 'File already exists.',
        7 : 'No such user.'
    }

    OPCODENAME = {
        RRQ : 'Read Request',
        WRQ : 'Write Request',
        DATA : 'Data block',
        ACK : 'Acknowledgement',
        ERROR : 'Error'
    }
    
    def __init__(self, header_buffer = None, **kkw):
        self.opcode = kkw.get ('opcode', 0)
        self.mode = kkw.get ('mode', 'octet')
        self.filename = kkw.get ('filename', None)
        self.blockno = kkw.get ('blockno', None)
        self.data = kkw.get ('data', None)
        self.errorcode = kkw.get ('errorcode', 0)
        self.errormessage = kkw.get ('errormessage', self.ERRORMESSAGE[self.errorcode] )
        self.valid = True
        if header_buffer: self.decode (header_buffer)
        
    def decode (self, header_buffer):        
        self.valid = True        
        try:
            (_,self.opcode) = struct.unpack_from ('BB', header_buffer )
            if self.opcode in [self.RRQ, self.WRQ]:
                try:
                    self.filename, self.mode, _ = header_buffer[2:].split('\0')
                except ValueError:
                    self.valid = False
            elif self.opcode == self.DATA:
                (self.blockno,) = struct.unpack_from('H', header_buffer[2:])
                self.blockno = socket.ntohs (self.blockno)
                self.data = header_buffer[4:]
            elif self.opcode == self.ERROR:
                (_,self.errorcode) = struct.unpack_from('BB', header_buffer[2:])
                self.errormessage = header_buffer[4:-1]
            elif self.opcode == self.ACK:
                (self.blockno,) = struct.unpack_from('H', header_buffer[2:])
                self.blockno = socket.ntohs (self.blockno)
            else:
                self.valid = False
        except struct.error:        
            self.valid = False
    
    def encode (self):
        binary = struct.pack ( 'BB', 0, self.opcode )
        if self.opcode in [self.RRQ, self.WRQ]:
            binary += self.filename + '\0' + self.mode + '\0'
        elif self.opcode in [self.DATA, self.ACK]:
            binary += struct.pack ('H', socket.htons(self.blockno) )
            if self.opcode == self.DATA:
                binary += self.data
        elif self.opcode == self.ERROR:
            binary += struct.pack ('BB', 0, self.errorcode)
            if self.errormessage is None: self.errormessage = self.ERRORMESSAGE[self.errorcode]
            binary += self.errormessage + '\0'
        return binary
    
    def __repr__(self):
        r = self.OPCODENAME[self.opcode]
        if self.opcode in [self.RRQ, self.WRQ]:
            r += ' [%s] %s' % (self.mode, self.filename )
        elif self.opcode  == self.ERROR:
            r += ' [%d] %s' % (self.errorcode, self.errormessage)
        elif self.opcode == self.DATA:
            r += ' #%d size:%db' % ( self.blockno, len(self.data) )
        return r
    
def read_data_source(stream, block_size=512):
    block = stream.read (block_size)
    while True:
        yield block
        if len(block) < block_size: return
        block = stream.read (block_size)            

class TFTPProtocolError(Exception):
    pass

@contextmanager
def ReverseTFTPConnection(client_address):
    s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
    s.connect (client_address)
    try:
        yield s
    finally:
        s.close()
        
def Handle_RRQ ( initiating_packet, client_address, data_source_stream, **kkw):
    stats = (0,0)
    total_data_sent = 0
    with ReverseTFTPConnection(client_address) as local_socket:
        (ipacket, opacket) = (Packet(), Packet())        
        local_socket.settimeout ( kkw.get ('timeout', 2) )
        
        opacket.opcode = Packet.DATA
        opacket.blockno = 1
    
        max_timeouts = kkw.get ( 'max_timeouts', 5 )
        max_bad_ack = kkw.get ( 'max_bad_ack', 3 )
        block_size = kkw.get ( 'block_size', 512 )
        
        timeouts = 0
        bad_ack = 0
        current_blockno = 1

        start_time = time()
               
        data_block = data_source_stream.read (block_size)        
        while True:
            opacket.data = data_block
            opacket.blockno = current_blockno
            local_socket.send ( opacket.encode() )
            total_data_sent += len(data_block)
        
            try:
                ipacket.decode ( local_socket.recv(4) )                
                timeouts = 0
            except socket.timeout:
                timeouts += 1
                if timeouts > max_timeouts:
                    raise TFTPProtocolError ( "RRQ {0} from {1}. Timeout waiting for ACK.".format(initiating_packet.filename, client_address) )
                continue
            
            if ipacket.opcode == Packet.ERROR:
                raise TFTPProtocolError ( "ERROR from {0}. ErrCode {1}, ErrMsg {2}".format (client_address, ipacket.errorcode, Packet.ERRORMESSAGE[ipacket.errorcode]))
            elif ipacket.opcode == Packet.ACK:
                if ipacket.blockno != current_blockno:
                    bad_ack += 1
                    if bad_ack > max_bad_ack:
                        raise TFTPProtocolError ("RRQ {0}. Too many ACKs out of sync.".format(initiating_packet.filename))
                    else:
                        continue
            else:
                raise TFTPProtocolError ("Unexpected opcode: {0} from {1}.".format (ipacket.opcode, client_address))
    
            if len(data_block) < block_size: break
            current_blockno += 1
            data_block = data_source_stream.read(block_size)
            
        dt = time() - start_time
        speed = total_data_sent / dt
        stats = (total_data_sent, dt, speed)
    return stats

def Handle_WRQ(initiating_packet, client_address):
    raise NotImplementedError

def Send_ERROR(client_address, error_code, error_message=None):
    with ReverseTFTPConnection(client_address) as local_socket:
        opacket = Packet ( opcode=Packet.ERROR, errorcode = error_code, errormessage = error_message )
        local_socket.send (opacket.encode())
        