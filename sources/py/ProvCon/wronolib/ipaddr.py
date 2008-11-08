#!/bin/env python
from socket import inet_aton as aton, inet_ntoa as ntoa, ntohl, htonl
from struct import unpack, pack

def str2ip4 (ip4str):
    return ntohl(unpack('I', aton(ip4str))[0])

def mask(prefixlen):
    return 0xffffffff ^ (2**(32 -prefixlen) - 1)

def ip_in_prefix (prefix, ip):
    (net,prlen) = prefix.split("/")
    prlen = int(prlen)    
    if prlen <= 0: return True
    
    m = mask(prlen)        
    net = str2ip4(net) & m
    ip = str2ip4(ip) & m
    return net == ip

class ip4addr:
    def __init__(self, ip):
        if type(ip) == str:
            self.addr = str2ip4(ip)
        elif type(ip) in [int, long]:            
            self.addr = ip
        elif isinstance(ip, ip4addr):
            self.addr = ip.addr
        else:
            self.addr = 0
    def __repr__(self):
        return ntoa(pack('I', htonl(self.addr)))
    
class ip4prefix(ip4addr):
    def __init__(self, ip, prefixlen):
        ip4addr.__init__(self, ip)
        self.prefixlen = max(0, min(32, prefixlen))
        self.mask = mask(self.prefixlen)
        self.network = self.addr & self.mask
        self.broadcast = self.addr | (self.mask ^ mask(32))        
        self.addr = self.network
        
    def get_network(self):
        return ip4addr ( self.network )

    def get_broadcast(self):
        return ip4addr ( self.broadcast )
    
    def contains(self, ip):
        if isinstance(ip, str):
            pr = ip4prefix (ip, self.prefixlen)
            return self.network == pr.network
        elif isinstance(ip, ip4addr):            
            return self.network == (ip.addr & self.mask)
        elif isinstance(ip, ip4prefix):
            pr = ip4prefix (ip.addr, self.prefixlen)
            return self.network == pr.network and self.prefixlen <= pr.prefixlen

    def __repr__(self):
        return "%s/%s" % (ntoa(pack('I', htonl(self.addr))), ntoa(pack('I', htonl(self.mask))) )

