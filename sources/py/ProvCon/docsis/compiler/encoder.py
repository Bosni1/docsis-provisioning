#!/bin/env python
from struct import unpack_from, pack_into, pack
from socket import htonl, htons
from libsnmp import rfc1155, rfc1157
import re

def __(*msg):
    pass
    
class error:
    def __init__(self, msg):
        self.msg = msg
    
    def __repr__(self):
        return "DOCSIS config compiler error: " + self.msg

def hex2bin(self, hexstr):
    binstr = ''
    
    
    
class tlv(object):
    """
    A basic Type-Length-Value record.
    """
    #_isComplex = False
    _canBeArray = False
    """Can this TLV hold and array of values"""
    _allowedValueTypes = [str, int, unicode]
    """A list of types of values that this TLV knows how to handle"""
    _typeName = "BASE_TLV"
    """For runtime type check"""
    _isTLV = True
    
    def __init__(self, **kkw):
        self._code = 0
        self._supercode = 0
        self._value = None
        
        self.code = kkw.get ( "code", None )
        self.value = kkw.get ( "value", None )
        self._uid = kkw.get ( "uid", None )

    def type_check (self, value):
        """
        Check if the value type is permitted.
        @rtype bool
        """
        return type(value) in self._allowedValueTypes
    
    def value_check(self, value):
        """
        Test if the given value can beassigned to this TLV.
        @rtype bool
        """
        return True

    def one_binary_value (self, oneval):
        """
        Convert the python object to its binary TLV representation, assuming
        it is a simple value.
        @type oneval: object
        @param oneval: the object to convert to binnary
        @rtype: str
        """
        return oneval
    
    def isset(self):
        """
        Check if all required fields are set on this TLV.
        @rtype: bool
        """
        return self._code is not None and self._value is not None
    
    def _code_set(self, code):
        if code is None: self._code = None
        elif code < 0 or code > 255:
            raise error ( "tlv code must be in (0,255)" )
        else:
            self._code = code
    def _code_get(self): 
        return self._code
    code = property(_code_get, _code_set)
    """Code, or "type" of the TLV. [0-255] int """

    def _value_filter(self, value):
        """
        Filter function applied to each new value.
        @type value: object
        @rtype: object
        """
        return value
    
    def _value_get(self): 
        return self._value
    def _value_set(self, value):         
        value = self._value_filter(value)
        if self.value_check(value): self._value = value
        else: raise error ("Invalid value '%s' for '%s'" % ( str(value), self.__class__.__name__ ) ) 
    value = property(_value_get, _value_set)
    """Value, the V in TLV"""
    
    def binary(self):
        """
        Return the binary form of this TLV.
        
        If this tlv is an array, or a complex value, recursively convert it to binary
        form.

        There are two possible scenarios when the value is an array:
           - _canBeArray is True, each element of the array is simply encoded as binary data
           - _canBeArray is False, each element is encoded as a separate TLV
                   
        @rtype: str
        """
        if self.code is None: return None
        content = ''
        if isinstance(self.value, list):
            if self._canBeArray:
                for v in self.value: content += self.one_binary_value ( v )
            else:
                for v in self.value: 
                    p = self.one_binary_value (v)
                    content += chr(self.code) + chr(len(p)) + p
                return content
        else:
            content = self.one_binary_value(self.value) 
        try:
            return chr(self.code) + chr(len(content)) + content
        except TypeError:
            raise error ( "cannot convert tlv to binary, TypeError" )
    
    def __reprval__(self):
        return `self.value`
    
    def __repr__(self):
        from tlvdef import TLV_NAME                
        lside = "DOCS_{0._typeName} #({0._supercode:d}, {0.code:d}) {1}".format (self, TLV_NAME.get(self._uid, "") , self._typeName)
        return lside.ljust(50) + " := " + self.__reprval__()

class tlv_generic(tlv):
    """
    TLV accepting string values.
    
    Strings can given in the "0x...." format as a hex binary string.
    """
    def _value_filter(self, value):
        realval = ""
        if isinstance(value, str):            
            if value.startswith("0x"):
                realval = "".join(map(lambda b: chr(int(b,16)), re.findall("([a-f0-9]{2})", value, re.I )))
            else:
                realval = val        
        return realval
    
class tlv_int (tlv):    
    _allowedValueTypes = [ int ]
    _typeName = "INT"
    def one_binary_value(self, v):
        return pack('l', htonl(v))
    
class tlv_uint(tlv): 
    _typeName = "UINT"
    _allowedValueTypes = [ int ]
    def one_binary_value(self, v):
        return pack('L', htonl(self.value))

class tlv_ushort(tlv):
    _typeName = "USHORT"
    _allowedValueTypes = [ int ]
    def value_check(self, value):
        return value in xrange(0,65536)    
    
    def one_binary_value(self, v):
        return pack('H', htons(self.value))

class tlv_uchar(tlv):
    _typeName = "UCHAR"
    _allowedValueTypes = [ int ]
    def value_check(self, value):
        return value >= 0 and value <= 255
    def one_binary_value(self, v):    
        return chr(self.value)
    
class tlv_snmp_value(tlv):
    """
    A generic SNMP TLV.
    
       >>> cfg.append.SNMP_MIB_OBJECT = ( ".1.3.6.1.2.1.1.6.0", rfc1155.OctetString("Value") )
    """
    _typeName = "SNMP"
    
    def value_check(self, value):
        #print value
        if not isinstance(value, tuple) or len(value) != 2:
            return False
        return True
    
    def one_binary_value(self, v):
        oid, val = v
        varbind = rfc1157.VarBind( rfc1155.ObjectID(oid), val )
        varbind = varbind.encode()
        return varbind
    
    def __reprval__(self):
        #o = rfc1155.OctetString()
        return self.value[0] + " = " + self.value[1].value

class tlv_oid (tlv):
    def one_binary_value(self, v):
        oid = rfc1157.ObjectID ( v )
        return oid.encode()

class tlv_ip(tlv):
    _typeName = "IP"
    _allowedValueTypes = [ str, unicode ]
    _canBeArray = True
    def check_value(self, value):
        def _check_ip(ipstr):
            return len ( [ int(i) for i in ipstr.split ( "." ) if int(i) >= 0 and int(i) <= 255 ] ) == 4
        try:
            if isinstance(value, list):
                for ipstr in value: 
                    if not _check_ip(ipstr): return False
                return True
            else:
                return _check_ip(value)
        except ValueError:
            pass
        return False
    
    def one_binary_value(self, ipstr):
        return "".join( [ chr(int(i)) for i in ipstr.split(".") ] )
        

class tlv_mac(tlv):
    _typeName = "MAC"
    _allowedValueTypes = [ str, unicode ]
    def one_binary_value(self, v):        
        binstr = "".join(map( lambda x: chr(int(x,16)), re.findall("([a-f0-9]{2})[\:\.]{0,1}", v, re.I )))
        return binstr[:6]

class tlv_string(tlv):
    _typeName = "STRING"
    _allowedValueTypes = [ str, unicode ]

class tlv_string_zero(tlv):
    """
    Zero terminated string.
    """
    _typeName = "STRING_Z"
    _allowedValueTypes = [ str, unicode ]
    def one_binary_value(self, v):
        return v + chr(0)
        
class tlv_tuple_2(tlv):
    def check_value(self, v):
        if isinstance(v, tuple):
            return len(v) == 2
        return False
    
    def one_binary_value(self, v):
        return chr(v[0]) + chr(v[1]) 

class tlv_tuple_3(tlv):
    def check_value(self, v):
        if isinstance(v, tuple):
            return len(v) == 3
        return False
    
    def one_binary_value(self, v):
        return chr(v[0]) + chr(v[1]) + chr(v[3])

class tlv_flow_qos (tlv_tuple_3):
    def one_binary_value(self, v):
        return chr ( v[0] + 2 * v[1] + 4 * v[2] )
    
    
class tlv_service_na(tlv):
    _typeName = "SV_NA"
    _allowedValueTypes = [ tuple ]
    def value_check(self, value):
        if isinstance(value, tuple):
            if len(tuple) == 3:
                c,t,cd = value
                return c >= 0 and c <= 255 and t >= 0 and t <= 255 and cd >= 0 and c<=255
            else:
                return False
        return False
    
    def one_binary_value(self, v):
        classid, typeid, codeid = v
        binstr = chr(classid) + chr(typeid) + chr(codeid)
        return binstr

class tlv_hex_string(tlv):
    _typeName = "HEXSTR"
    _allowedValueTypes = [ str, unicode ]
    
    def one_binary_value(self, v):
        binstr = ''
        hexstr = str(v)
        while len(hexstr) > 1:
            byte = hexstr[:2]
            hexstr = hexstr[2:]
            try:
                binstr += chr(int(byte, 16))
            except ValueError:
                raise error ( "Invalid hex string: '%s'" % v )
        return binstr

class tlv_cvc_data (tlv_hex_string):
    _typeName = "CVC"
    def _filter_value(self, value):
        if len(value) < 255: return value
        else:
            self.value = []
            for p in range(0,len(value),254):
                self.value.append ( p[p:p+254] )

class tlv_subscriber_mgmt(tlv):
    def _check_value(self, value):
        pass
                
class tlv_subclass(object):
    """
    For record-structured (multipart) TLVs, this class provides a clean interface, allowing
    a quick and pretty access to its fields:

       >>> cos = cfg.CLASS_OF_SERVICE
       >>> cos.CLASS_ID = 1
       >>> cos.CLASS_MAX_RATE_DOWN = 4000000
       
       >>> dcl = tlv_down_packet_classifier()
       >>> dcl.CLASSIFIER_REFERENCE = 1
       >>> dcl.CLASSIFIER_IDENTIFIER = 1
       >>> cfg.append.ANY = dcl
 
    """ 
    def __init__(self, definition, parentuid):
        self._definition = definition
        self._opt_dict = {}
        self._uid = parentuid        
        for df in self._definition:
            tpl = self._definition[df]
            parent = tpl[0]
            if isinstance(parent, list):
                if self._uid in parent:
                    self._opt_dict[df] = tpl        
            elif parent == self._uid:
                self._opt_dict[df] = tpl        
                    
    def __setattr__(self, attrname, val):        
        if attrname.startswith("_"):
            return object.__setattr__(self, attrname, val)
        elif attrname in self.__dict__: 
            return object.__setattr__(self, attrname, val)
        elif attrname in self._opt_dict:
            tpl = self._opt_dict[attrname]            
            return self.set_option ( attrname, tpl, val)
        else:            
            raise AttributeError ( attrname )
        
    def __getattr__(self, attrname):
        
        if attrname.startswith("_"):
            return object.__getattr__(self, attrname)
        if attrname in self.__dict__: 
            return object.__getattr__(self, attrname)
        elif attrname in self._opt_dict:
            tpl = self._opt_dict[attrname]            
            return self.get_option ( tpl, attrname)
        else:
            raise AttributeError ( attrname )

    def __delattr__(self, attrname):
        if attrname.startswith("_"):
            return object.__delattr__(self, attrname)
        if attrname in self.__dict__: 
            return object.__delattr__(self, attrname)
        elif attrname in self._opt_dict:
            del self[attrname]            
        else:
            raise AttributeError ( attrname )
        
            
class tlv_multipart(tlv):
    """
    A record-structured TLV.
    Supports iteration over sub-tlvs.
    """
    class iterator:
        def __init__(self, multipart):            
            self.multipart = multipart
            self.keys = iter(self.multipart._korder)
            
        def next(self):
            key = self.keys.next()
            return self.multipart._kvalues[key]
    
    class append_proxy(object):
        def __init__(self, multipart):
            from tlvdef import DOCSIS_TLV
            self._multipart = multipart
            self._docs = DOCSIS_TLV

        def __getattr__(self, attrname):            
            x = self.__setattr__(attrname, None)
            return x
        
        def __setattr__(self, attrname, value):            
            if attrname.startswith("_"):
                return object.__setattr__(self, attrname, value)
            elif attrname == "ANY":
                return self._multipart.append_option ( None, value )                                
            elif attrname == "GENERIC":
                code, val = value
                opt = tlv_generic ( code=code, value=val )
                return self._multipart.append_option (None, opt)                
            
            try:                
                return self._multipart.append_option ( self._docs[attrname], value )                            
            except KeyError:
                raise AttributeError ( attrname )
            
    def __init__(self, **kkw):
        self._code = kkw.get("code", 0)
        self._uid = kkw.get("uid", 0)
        self._supercode = 0
        self._kvalues = {}
        self._korder = []
        self._uniqid = 1000000
        self._append = tlv_multipart.append_proxy(self)
        
    def set_option(self, name, odef, value):
        __ ( id(self), "set_option", name )
        if issubclass(value.__class__, tlv):
            self[name] = value
        else:
            pid, mid, enccls, predicate, valuefilter, uid = odef            
            if not predicate(valuefilter(value)):                
                raise ValueError ( name, value )
            self[name] = enccls ( code=mid, value = valuefilter(value), uid=uid )
        
        return self[name]
    
    def append_option(self, odef ,value):
        self._uniqid += 1
        return self.set_option (self._uniqid, odef, value)
        
        
    def get_option(self, odef, optname):                
        if optname in self:        
            return self[optname]
        else:            
            odef[0] == self._uid
            try:
                self.set_option (optname, odef, None)
            except ValueError:                
                import sys
                print sys.exc_info()[:2]
                return None
            return self[optname]
                
        
    def _get_values(self): return None
    value = property(_get_values)

    def __contains__(self, optname):
        return optname in self._kvalues
    
    def __setitem__(self, key, value):
        #if key in self._korder: self._korder.remove(key)
        __( id(self), "__setitem__", key, id(value))        
        self._kvalues[key] = value                
        if key not in self._korder: self._korder.append ( key )
        __( id(self), "_korder", self._korder)
        value._supercode = self._uid
    
    def __getitem__(self, key):        
        try:
            return self._kvalues[key]
        except KeyError:
            print "KeyError", key, self._korder
            return None
    
    def __iter__(self):
        return tlv_multipart.iterator(self)
        #return iter(self._values + self._kvalues.values() )
    
    def _append_proxy (self):
        return self._append
    append = property(_append_proxy)
        
    def __delitem__(self, key):
        if isinstance(key, int):
            del self._kvalues[ self._korder [ key ] ]
        else:
            del self._kvalues[key]
        self._korder.remove (key)
    
    def contents(self):
        bin = ''
        for tlv in self:
            if isinstance(tlv, list):
                binarray = map (lambda x: x.binary(), tlv)
                bin += "".join(binarray)
            else:
                bin += tlv.binary()       
        return bin
    
    def binary(self):
        contents = self.contents()
        return chr(self.code) + chr(len(contents)) + contents
    
    def __repr__(self):
        from tlvdef import TLV_NAME
        r = ''
        sign = (self._supercode, self._code)
        r += "DOCSIS_SUBCLASS {0}\n".format ( TLV_NAME.get ( self._uid, str(self._uid) ) )
        for i in self: r += `i` + "\n"
        return r
    
class tlv_multipart_subclass(tlv_multipart, tlv_subclass):
    def __init__(self, **kkw):
        from tlvdef import DOCSIS_TLV, DefaultValues, TLV_NAME
        tlv_multipart.__init__(self, **kkw)
        tlv_subclass.__init__(self, DOCSIS_TLV, self._uid)
        
        skip_defaults = kkw.get("add_defaults", False)        
        if not skip_defaults:            
            dv = DefaultValues.get ( TLV_NAME[self._uid], {})
            __ ( id(self), " __initvars__" )
            for vn, vv in dv: self.__setattr__( vn, vv )
            __ ( id(self), " endof__initvars__" )

def generic_multipart_subclass(tlv_name):
    class _generic(tlv_multipart_subclass):
        def __init__(self, **kkw):            
            from tlvdef import TLV_CODE, TLV_ID
            tlv_multipart_subclass.__init__(self, code=TLV_CODE[tlv_name], uid=TLV_ID[tlv_name] )
    return _generic

tlv_class_of_service = generic_multipart_subclass ( "CLASS_OF_SERVICE" )
tlv_baseline_privacy = generic_multipart_subclass ( "BASELINE_PRIVACY" )
tlv_capabilities = generic_multipart_subclass ( "CAPABILITIES" )
tlv_telephone = generic_multipart_subclass ( "TELEPHONE" )
tlv_up_packet_classifier = generic_multipart_subclass ( "UPSTREAM_PACKET_CLASSIFIER" )
tlv_down_packet_classifier = generic_multipart_subclass ( "DOWNSTREAM_PACKET_CLASSIFIER" )

tlv_error = None

tlv_classifier_ip = generic_multipart_subclass ( "CLASSIFIER_IP_PACKET" )
tlv_classifier_ether = generic_multipart_subclass ( "CLASSIFIER_ETHERNET" )
tlv_classifier_ieee = generic_multipart_subclass ( "CLASSIFIER_IEEE" )

tlv_flow_up = generic_multipart_subclass ( "FLOW_UP" )
tlv_flow_down = generic_multipart_subclass ( "FLOW_DOWN" )

tlv_vendor = generic_multipart_subclass ( "VENDOR" )
tlv_phs = generic_multipart_subclass ( "PHS" )
tlv_snmp_v3_kickstart = generic_multipart_subclass ( "SNMP_V3_KICKSTART" )
tlv_snmp_v3_trap = generic_multipart_subclass ( "SNMP_V3_TRAP" )

