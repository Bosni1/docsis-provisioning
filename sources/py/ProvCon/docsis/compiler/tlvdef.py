#!/bin/env python

from encoder import *
from subclass import *
from libsnmp import rfc1155

__all__ = [ "DOCSIS_TLV", "TLV_NAME", "TLV_CODE", "TLV_ID", "TLV_PARENT", "TLV_PARENT_NAME", "DefaultValues" ]

def partial (fn, *givenargs, **gkkw):
    def _apply(*args, **kkw):        
        kwarg = {}
        for k in gkkw: kwarg[k] = gkkw[k]
        for k in kkw: kwarg[k] = kkw[k]
        return fn ( *(givenargs + args), **kwarg )
    return _apply

def isipaddress(ipstr):
    try:
        return len("".join( map ( lambda x: chr(int(x)), ipstr.split(".") )) ) == 4
    except ValueError:
        return False

def identity(v): return v
def truth(v): return True
def asboolean(v): return int(bool(v))

def istuple(n):
    def _check(tpl):
        if isinstance(tpl, tuple):
            return len(tpl) == n
        return False
    return _check

def int_range_check (v1, v2):
    def check(v):
        return v >= v1 and v <= v2
    return check

def string_length_check(l1, l2):
    def check(v):
        return len(v) >= l1 and len(v) <= l2
    return check

def snmpval(cls):
    def _cls(val):
        return cls(val)
    return _cls



def tlv_subclass_code (code):
    return partial ( tlv_multipart_subclass, code=code ) 


DOCSIS_TLV = {
"MAIN" : (0,0, tlv_multipart, truth, identity, 0 ),
"DOWNSTREAM_FREQUENCY" : (0, 1, tlv_uint, int_range_check(88000000, 860000000), identity, 10100 ),
"UPSTREAM_CHANNEL_ID" : (0, 2, tlv_uchar, truth, identity, 10200),
"NETWORK_ACCESS" : (0, 3, tlv_uchar, truth, asboolean, 10300 ),
"CLASS_OF_SERVICE" : (0, 4, tlv_class_of_service, truth, identity, 10400),
   "CLASS_ID" : (10400, 1, tlv_uchar, truth, identity, 10401),
   "CLASS_MAX_RATE_DOWN" : (10400, 2, tlv_uint, int_range_check (0, 52000000), identity, 10402 ),
   "CLASS_MAX_RATE_UP" : (10400, 3, tlv_uint, int_range_check(0, 10000000), identity, 10403),
   "CLASS_PRIORITY_UP" : (10400, 4, tlv_uchar, int_range_check(0, 7), identity, 10404),
   "CLASS_GUARANTEED_UP" : (10400, 5, tlv_uint, int_range_check(0, 10000000), identity, 10405),
   "CLASS_MAX_BURST_UP" : (10400, 6, tlv_ushort, truth, identity, 10406),
   "CLASS_PRIVACY_ENABLE" : (10400, 7, tlv_uchar, truth, asboolean, 10407 ),
"CAPABILITIES": (0, 5, tlv_capabilities, truth, identity, 10500),
    "CAPABILITIES_CONCENTRATION": (10500, 1, tlv_uchar, truth, asboolean, 15001),
    "CAPABILITIES_VERSION": (10500,2, tlv_uchar, truth, asboolean, 15002),
    "CAPABILITIES_FRAGMENTATION": (10500,3, tlv_uchar, truth, asboolean, 15003),
    "CAPABILITIES_PAYLOAD_HEADER": (10500,4, tlv_uchar, truth, asboolean, 15004),
    "CAPABILITIES_IGMP": (10500,5, tlv_uchar, truth, asboolean, 15005),
    "CAPABILITIES_PRIVACY": (10500,6, tlv_uchar, truth, identity, 15006),
    "CAPABILITIES_DOWNSTREAM_SAID": (10500,7, tlv_uchar, truth, identity, 15007),
    "CAPABILITIES_UPSTREAM_SID": (10500,8, tlv_uchar, truth, identity, 15008),
    "CAPABILITIES_FILTER": (10500,9, tlv_uchar, int_range_check(0,3), identity, 15009),
    "CAPABILITIES_TRANSMIT_EQUALIZER_TAPS_PER_SYMBOL": (10500,10, tlv_uchar, int_range_check(1,4), asboolean, 15010),
    "CAPABILITIES_TRANSMIT_EQUALIZER_TAPS": (10500,11, tlv_uchar, int_range_check(8,64), asboolean, 15011),
    "CAPABILITIES_DCC": (10500,12, tlv_uchar, truth, asboolean, 15012),
"CM_MIC" : (0, 6, tlv_hex_string, truth, identity, 10600 ),
"CMTS_MIC" : (0, 7, tlv_hex_string, truth, identity, 10700  ),
"SOFTWARE_UPGRADE_FILENAME" : (0, 9, tlv_string, truth, identity, 10900),
"SNMP_WRITE_CONTROL" : (0, 10, tlv_string, truth, identity, 11000),  #!!!
"SNMP_MIB_OBJECT" : (0, 11, tlv_snmp_value, truth, identity,11100), 
"MODEM_ADDRESS" : (0, 12, tlv_ip, truth, identity,11200),  
"SERVICES_NOT_AVAILABLE" : (0, 13, tlv_service_na, truth, identity,11300),  
"CPE_ETHERNET" : (0, 14, tlv_mac, truth, identity,11400),  
"TELEPHONE": (0, 15, tlv_telephone, truth, identity, 11500),
    "TELEPHONE_PROVIDER": (11500, 2, tlv_string, truth, identity, 11502),
    "TELEPHONE_NUMBER_1": (11500, 3, tlv_string, truth, identity, 11503),
    "TELEPHONE_NUMBER_2": (11500, 4, tlv_string, truth, identity, 11504),
    "TELEPHONE_NUMBER_3": (11500, 5, tlv_string, truth, identity, 11505),
    "TELEPHONE_CON_THRESH": (11500, 6, tlv_string, truth, identity, 11506),
    "TELEPHONE_LOGIN": (11500, 7, tlv_string, truth, identity, 11507),
    "TELEPHONE_PASSWORD": (11500, 8, tlv_string, truth, identity, 11508),
    "TELEPHONE_DHCP_AUTH": (11500, 9, tlv_uchar, truth, asboolean, 11509),
    "TELEPHONE_DHCP_SERVER": (11500, 10, tlv_ip, isipaddress, identity, 11510),
    "TELEPHONE_RADIUS_REALM": (11500, 11, tlv_string, truth, identity, 11511),
    "TELEPHONE_PPP_AUTH": (11500, 11500, 12, tlv_uchar, truth, identity, 11512),
    "TELEPHONE_DDI_TIMER_TESH" : (11500, 13, tlv_uint, truth, identity, 11513),
"BASELINE_PRIVACY" : (0, 17, tlv_baseline_privacy, truth, identity, 11700),
    "BP_AUTH_TIMEOUT" : (11700, 1, tlv_uint, int_range_check(1, 30), identity, 11701),
    "BP_REAUTH_TIMEOUT" : (11700, 2, tlv_uint, int_range_check(1, 30), identity, 11702),
    "BP_AUTH_GRACE" : (11700, 3, tlv_uint, int_range_check(1, 6047999), identity, 11703),
    "BP_OP_TIMEOUT" : (11700, 4, tlv_uint, int_range_check(1, 10), identity, 11704),
    "BP_REKEY_TIMEOUT" : (11700, 5, tlv_uint, int_range_check(1, 10), identity, 11705),
    "BP_TEK_GRACE_TIMEOUT" : (11700, 6, tlv_uint, int_range_check(1, 302399), identity, 11706),
    "BP_AUTH_REJECT_TIMEOUT" : (11700, 7, tlv_uint, int_range_check(1, 600), identity, 11707),
    "BP_SA_MAP_TIMEOUT" : (11700, 8, tlv_uint, int_range_check(1, 10), identity, 11708),
    "BP_SA_MAX_RETRIES" : (11700, 9, tlv_uint, int_range_check(0, 10), identity, 11709),
"MAX_CPE" : (0, 18, tlv_uchar, int_range_check(1,254), identity,11800),  
"TFTP_TIMESTAMP" : (0, 19, tlv_uint, truth, identity,11900),  
"TFTP_ADDRESS" : (0, 20, tlv_ip, truth, identity,12000),  
"SOFTWARE_TFTP_ADDRESS" : (0, 21, tlv_ip, truth, identity,12100),  
"UPSTREAM_PACKET_CLASSIFIER": (0, 22, tlv_up_packet_classifier, truth, identity, 12200),
"DOWNSTREAM_PACKET_CLASSIFIER": (0, 23, tlv_down_packet_classifier, truth, identity, 12300),
    "CLASSIFIER_REFERENCE": ( [12200, 12300], 1, tlv_uchar, int_range_check(1,255), identity, 522010),
    "CLASSIFIER_IDENTIFIER": ( [12200, 12300], 2, tlv_ushort, int_range_check(1,65535), identity, 522020),
    "CLASSIFIER_FLOW_REFERENCE": ( [12200, 12300], 3, tlv_ushort, int_range_check(1,65535), identity, 522030),
    "CLASSIFIER_FLOW_IDENTIFIER": ( [12200, 12300], 4, tlv_uint, int_range_check(1,4294967295), identity, 522040), 
    "CLASSIFIER_RULE_PRIORITY": ( [12200, 12300], 5, tlv_uchar, truth, identity, 522050),
    "CLASSIFIER_ACTIVATION_STATE": ( [12200, 12300], 6, tlv_uchar, truth, asboolean, 522060),
    "CLASSIFIER_DSC_ACTION": ( [12200, 12300], 7, tlv_uchar, int_range_check(0,2), identity, 522070),
    "CLASSIFIER_ERROR": ( [12200, 12300], 8, tlv_error, truth, identity, 522080),
    "CLASSIFIER_IP_PACKET": ( [12200, 12300], 9, tlv_classifier_ip, truth, identity, 522090),
        "IP_TOS": (522090, 1, tlv_tuple_3, istuple(3), identity, 522901),
        "IP_PROTOCOL": (522090, 2, tlv_ushort, int_range_check(0, 257), identity, 522902),
        "IP_ADDRESS": (522090, 3, tlv_ip, isipaddress, identity, 522903),
        "IP_MASK": (522090, 4, tlv_ip, isipaddress, identity, 522904),
        "IP_DEST_ADDRESS": (522090, 5, tlv_ip, isipaddress, identity, 522905),
        "IP_DEST_MASK": (522090, 6, tlv_ip, isipaddress, identity, 522906),
        "IP_SOURCE_PORT_START": (522090, 7, tlv_ushort, int_range_check(0,65535), identity, 522907),
        "IP_SOURCE_PORT_END": (522090, 8, tlv_ushort, int_range_check(0,65535), identity, 522907),
        "IP_PORT_START": (522090, 9, tlv_ushort, int_range_check(0,65535), identity, 522907),
        "IP_DEST_PORT_END": (522090, 10, tlv_ushort, int_range_check(0,65535), identity, 522907),
   "CLASSIFIER_ETHERNET": ( [12200, 12300], 10, tlv_classifier_ether, truth, identity, 522100),
        "ETHERNET_DEST_MAC": (522100, 1, tlv_mac, truth, identity, 522101),        
        "ETHERNET_SOURCE_MAC": (522100, 2, tlv_mac, truth, identity, 522102),       
        "ETHERNET_DSAP_TYPE": (522100, 3, tlv_tuple_3, istuple(3), identity, 522103),
    "CLASSIFIER_IEEE": ( [12200, 12300], 11, tlv_classifier_ieee, truth, identity, 522110),
        "USER_PRIORITY": (522110, 1, tlv_tuple_2, istuple(2), identity, 522111),
        "VLAN_ID": (522110,2, tlv_ushort, truth, identity, 522112),
"FLOW_UP": (0, 24, tlv_flow_up, truth, identity, 12400),
    "FLOW_IDENTIFIER_2": (12400, 3, tlv_ushort, int_range_check(1, 16383), identity, 12403),
    "FLOW_MAX_CONCAT_BURST": (12400, 14, tlv_ushort, truth, identity, 12414),
    "FLOW_SCHED_TYPE": (12400, 15, tlv_uchar, int_range_check(1,6), identity, 12415),
    "FLOW_REQUEST_POLICY": (12400, 16, tlv_uint, int_range_check(0,511), identity, 12416),
    "FLOW_POLLING_INTERVAL": (12400, 17, tlv_uint, truth, identity, 12417),
    "FLOW_POLL_JITTER": (12400, 18, tlv_uint, truth, identity, 12418),
    "FLOW_UNSOLICITED_GRANT_SIZE": (12400, 19, tlv_ushort, truth, identity, 12419),
    "FLOW_NOMINAL_GRANT_SIZE": (12400, 20, tlv_uint, truth, identity, 12420),
    "FLOW_GRANT_JITTER": (12400, 21, tlv_uint, truth, identity, 12421),
    "FLOW_GRANTS_PER_INTERVAL": (12400, 22, tlv_uchar, int_range_check(0,127), identity, 12422),
    "FLOW_TOS_MASK": (12400, 23, tlv_tuple_2, istuple(2), identity, 12423),
    "FLOW_UNSOLICITED_GRANT_TIME": (12400, 24, tlv_uint, truth, identity, 12424),
"FLOW_DOWN": (0, 25, tlv_flow_down, truth, identity, 12500),
    "FLOW_MAX_DOWN_LATENCY": (12500, 14,  tlv_uint, truth, identity, 12514),
#shared by flow up / down
    "FLOW_REFERENCE": ( [12400, 12500], 1, tlv_ushort, int_range_check(1,65535), identity, 60001),
    "FLOW_IDENTIFIER": ( [12400, 12500],2, tlv_uint, int_range_check(1,2**32 -1), identity, 60002),
    "FLOW_CLASS_NAME": ( [12400, 12500],4,tlv_string_zero, truth, identity, 60004),
    "FLOW_ERROR": ( [12400, 12500],5,tlv_error, truth, identity, 60005),
    "FLOW_QOS": ( [12400, 12500],6,tlv_flow_qos, istuple(3), identity, 60006),
    "FLOW_TRAFFIC_PRIORITY": ( [12400, 12500],7,tlv_uchar, int_range_check(0,7), identity, 60007),
    "FLOW_MAX_RATE": ( [12400, 12500],8,tlv_uint, truth, identity, 60008),
    "FLOW_MAX_BURST": ( [12400, 12500],9,tlv_uint, int_range_check(1521,2**32-1), identity, 60009),
    "FLOW_MIN_RESERVED_RATE": ( [12400, 12500],10,tlv_uint, truth, identity, 60010),
    "FLOW_MIN_RESERVED_PACKET_SIZE": ( [12400, 12500],11,tlv_ushort, truth, identity, 60011),
    "FLOW_ACTIVE_QOS_TIMEOUT": ( [12400, 12500],12,tlv_ushort, truth, identity, 60012),
    "FLOW_ADMITTED_QOS_TIMEOUT": ( [12400, 12500],13,tlv_ushort, truth, identity, 60013),
    "FLOW_VENDOR": ( [12400, 12500],43,tlv_vendor, truth, identity, 60043),
"PHS": (0, 26, tlv_phs, truth, identity, 12600),
    "PHS_CLASSIFIER_REFERENCE": (12600, 1, tlv_uchar, int_range_check(1,255), identity, 12601),
    "PHS_CLASSIFIER_IDENTIFIER": (12600, 2, tlv_ushort, int_range_check(1,65535), identity, 12602),
    "PHS_SERVICE_FLOW_REFERENCE": (12600, 3, tlv_ushort, int_range_check(1,65535), identity, 12603),
    "PHS_SERVICE_FLOW_IDENTIFIER": (12600, 4, tlv_uint, int_range_check(1,2**32-1), identity, 12604),
    "PHS_DSC_ACTION": (12600, 5, tlv_uchar, int_range_check(0,3), identity, 12605),
    "PHS_ERROR": (12600, 6, tlv_error, truth, identity, 12606),
    "PHS_PHSF": (12600, 7, tlv_string, truth, identity, 12607),
    "PHS_PHSI": (12600, 8, tlv_uchar, int_range_check(1,255), identity, 12608),
    "PHS_PHSM": (12600, 9, tlv_string, truth, identity, 12609),
    "PHS_PHSS": (12600, 10, tlv_uchar, truth, identity, 12610),
    "PHS_PHSV": (12600, 11, tlv_uchar, int_range_check(0,1), identity, 12611),    
"HMAC_DIGEST" : (0, 27, tlv_hex_string, truth, identity,12700),  
"MAX_CLASSIFIERS" : (0, 28, tlv_ushort, truth, identity,12800),  
"PRIVACY_ENABLE" : (0, 29, tlv_uchar, truth, asboolean,12900),  
"AUTHORIZATION_BLOCK" : (0, 30, tlv_hex_string, truth, identity,13000),  
"KEY_SEQUENCE" : (0, 31, tlv_uchar, int_range_check(0,15), identity,13100),  
"MFG_CVC_DATA" : (0, 32, tlv_cvc_data, truth, identity, 13200),  
"COS_CVC_DATA" : (0, 33, tlv_cvc_data, truth, identity,13300),  
"MTA_CONFIG_DELIMITER" : (0, 254, tlv_string, truth, identity,25400),  #!!!
"SNMP_V3_KICKSTART": (0, 34, tlv_snmp_v3_kickstart, truth, identity,13400),
    "SECURITY_NAME": (13400, 1, tlv_string, string_length_check(2,16), identity, 13401),
    "MANAGER_PUBLIC_NUMBER": (13400, 2, tlv_hex_string, truth, identity, 13402),
"SNMP_V3_TRAP": (0, 38, tlv_snmp_v3_trap, truth, identity, 13800),
    "TRAP_ADDRESS": (13800, 1, tlv_ip, isipaddress, identity, 13801),
    "TRAP_PORT": (13800,2,tlv_ushort, truth, identity, 13802),
    "TRAP_TYPE": (13800,3,tlv_ushort, int_range_check(1,5), identity, 13803),
    "TRAP_TIMEOUT": (13800,4,tlv_ushort, truth, identity, 13804),
    "TRAP_RETRIES": (13800,5,tlv_ushort, int_range_check(0,255), identity, 13805),
    "TRAP_FILTER": (13800,6,tlv_oid, truth, identity, 13806),    
    "TRAP_SECURITY_NAME": (13800,7,tlv_string, string_length_check(2,16), identity, 13807),
"SUBSCRIBER_MANAGEMENT" : (0, 35, tlv_subscriber_mgmt, truth, identity,13500),  
"SUBSCRIBER_MANAGEMENT_CPE_IP" : (0, 36, tlv_ip, truth, identity,13600),  
"SUBSCRIBER_MANAGEMENT_FILTER" : (0, 37, tlv_string, truth, identity,13700),  #!!!
"COSIGNER_CODE_CERTIFICATE" : (0, 33, tlv_string, truth, identity,13300),  
"DOCSIS_2_ENABLE" : (0, 39, tlv_uchar, truth, asboolean,13900),  #!!!           
"VENDOR": (0, 43, tlv_vendor, truth, identity, 14300),
    "VENDOR_ID": (14300, 8, tlv_hex_string, truth, identity, 14308),
}

DefaultValues = {
   "BASELINE_PRIVACY" : [
      ("BP_AUTH_TIMEOUT", 10),
      ("BP_REAUTH_TIMEOUT" , 10),
      ("BP_AUTH_GRACE" , 600),
      ("BP_OP_TIMEOUT" , 10),
      ("BP_REKEY_TIMEOUT" , 10),
      ("BP_TEK_GRACE_TIMEOUT" , 600),
      ("BP_AUTH_REJECT_TIMEOUT" , 60),
   ],
   "UPSTREAM_PACKET_CLASSIFIER" : [
       ("CLASSIFIER_ACTIVATION_STATE", 1),
   ],
   "DOWNSTREAM_PACKET_CLASSIFIER" : [
       ("CLASSIFIER_ACTIVATION_STATE", 1),      
   ],
   "FLOW_DOWN": [
       ("FLOW_REFERENCE" , 1),
       ("FLOW_QOS" , (1,1,1)),       
   ]
}

TLV_NAME = {}
for n in DOCSIS_TLV: TLV_NAME[DOCSIS_TLV[n][5]] = n

TLV_CODE = {}
for n in DOCSIS_TLV: TLV_CODE[n] = DOCSIS_TLV[n][1] 

TLV_ID = {}
for n in DOCSIS_TLV: TLV_ID[n] = DOCSIS_TLV[n][5] 

TLV_PARENT = {}
for n in DOCSIS_TLV: TLV_PARENT[DOCSIS_TLV[n][5] ] = DOCSIS_TLV[n][0] 

TLV_PARENT_NAME = {}
for n in DOCSIS_TLV: 
    try:
        TLV_PARENT_NAME[n] = TLV_NAME[TLV_PARENT[DOCSIS_TLV[n][5]]]
    except:
        pass

