#!/bin/env python

from encoder import *
from tlvdef import *
from hashlib import md5

class config(tlv_multipart_subclass):
    def __init__(self,key=None):
        tlv_multipart_subclass.__init__(self, code=0, uid=0)
        self._key = key
            
    def binary(self):        
        content = self.contents()        
        cm_mic = md5( content ).hexdigest()  
        cmts_mic = cm_mic
        self.CM_MIC = cm_mic
        #self.set_option ("CMTS_MIC", cmts_mic)
        content = self.contents()        
        content += chr(0) * (4 - len(content) % 4)
        return content

    def output (self, ostream):
        ostream.write ( self.binary() )    
    
    def get_cm_mic(self):
        pass    
    
cfg = config()
cfg.NETWORK_ACCESS = 1
cfg.DOWNSTREAM_FREQUENCY = 410000000
cfg.TFTP_ADDRESS = "10.1.0.1"
cfg.append.MAX_CPE = 3
cfg.SOFTWARE_UPGRADE_FILENAME = "upgrade.hex"

cos = cfg.CLASS_OF_SERVICE
cos.CLASS_ID = 1
cos.CLASS_MAX_RATE_DOWN = 4000000

#cfg.append.CLASS_OF_SERVICE = cos

cfg.BASELINE_PRIVACY.BP_TEK_GRACE_TIMEOUT = 5

cfg.append.CPE_ETHERNET = "00:22:33:44:55:66"
cfg.append.SNMP_MIB_OBJECT = ( ".1.3.6.1.2.1.1.6.0", rfc1155.OctetString("dupa") )

dcl = tlv_down_packet_classifier()
dcl.CLASSIFIER_REFERENCE = 1
dcl.CLASSIFIER_IDENTIFIER = 1

cfg.append.ANY = dcl

vendor = cfg.VENDOR
vendor.VENDOR_ID = "ffeedd"
vendor.append.GENERIC = (188, "0xfffffffffedece")

flow = cfg.append.FLOW_DOWN
flow.FLOW_REFERENCE = 100

flow = cfg.append.FLOW_UP
flow.FLOW_REFERENCE = 1

print cfg
with open('cm.cfg', 'w') as f:
    cfg.output ( f )

