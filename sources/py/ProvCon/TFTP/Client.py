#!/bin/env python

from Protocol import Packet
import socket

__all__ = ["TFTPC", "stress_test"]

def TFTPC (address, port, filename, ostream):
    
    init_socket = socket.socket ( socket.AF_INET, socket.SOCK_DGRAM )    
    
    init_packet = Packet( opcode = Packet.RRQ, filename=filename )
    init_socket.sendto ( init_packet.encode(), (address, port) )        
    

    (buff, (raddress, rport)) = init_socket.recvfrom (516)
    dat_packet = Packet ( buff )
    ack_packet = Packet ( opcode = Packet.ACK )
    current_block = 1
    
    
    while 1:        
        dat_packet.decode ( buff )
        ostream.write ( dat_packet.data )
        
        ack_packet.blockno = dat_packet.blockno        
        init_socket.sendto ( ack_packet.encode(), (raddress, rport ) )
            
        if len(dat_packet.data) < 512: break

        (buff, (traddress, trport)) = init_socket.recvfrom (516)
        if traddress != raddress or trport != rport: raise Exception ( "Security error!" )

    
    init_socket.close()
    
def stressing_tester ( queue_from, queue_to ):
    from StringIO import StringIO
    import Queue as ThQueue
    try:
        while 1:
            (no, addr, port, filename) = queue_from.get_nowait()
            print no
            try:
                TFTPC (addr, port, filename, StringIO() )
            except:
                continue
            queue_to.put ( no )
    except ThQueue.Empty:
        pass
        

def stress_test ( addr, port, filename, totalcount, processes):
    from multiprocessing import Process, Queue
    import Queue as ThQueue
    qfrom = Queue()
    qto = Queue()
    
    for i in xrange(0,totalcount): qfrom.put ( (i, addr, port, filename) )
    p = [Process(target=stressing_tester, args=(qfrom,qto))  for i in range (0, processes)]
    map (lambda x: x.start(), p)
    map (lambda x: x.join(), p)
    try:
        while True:
            print qto.get_nowait()
    except ThQueue.Empty:
        pass        



