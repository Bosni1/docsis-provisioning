#!/bin/env python
##$Id$

class cablemodem(object):

    class _mac(object):
        def __init__(self, **kkw):
            self.ethernet = kkw.get ( 'ethernet', None )
            self.hfc = kkw.get ( 'hfc', None )
            self.usb = kkw.get ( 'usb', None )
            self.lan = kkw.get ( 'lan', None )
            self.wan = kkw.get ( 'wan', None )

    class _cpe(object):
        def __init__(self, **cpe):
            self.ip = cpe.get ( 'ip', None )
            self.mac = cpe.get ( 'mac', None)
            
    class _cos(object):
        def __init__(self, **cos):
            self.upload = cos.get ( "upload", 0 )
            self.download = cos.get ( "download", 0 )
            self.priority = cos.get ( "prio", 0 )
            self.nightsurf = cos.get ( "nightsurf", False )
            
    def __init__(self, **kkw):
        self.active = kkw.get ( 'active', 0 )        
        self.mac = self._mac ( ** kkw.get ( 'mac', {} ) )
        self.docsis_version = kkw.get ( "docsis_version", 1.0 )
        self.mgmt_ip = kkw.get ( "mgmt_ip", None )
        self.cpe = [self._cpe (i) for i in kkw.get ( 'cpe', [] )]
        self.firewall = kkw.get ( "firewall", True )
        self.maxcpe = kkw.get ( "maxcpe", None )
        self.snmpwrite = kkw.get ( "snmpwrite", [] )
        self.cos = self._cos ( ** kkw.get ( "cos", {} ) )
        
from template import RunTemplate
from StringIO import StringIO
#cm = {
#    'active': 1
#}
cm = cablemodem()
of = StringIO()
RunTemplate ( 'template_test.t.py', of, cm )
print of.getvalue()
