import rObject
from ProvCon.dbui.database import CFG
from ProvCon.dbui.orm import GenericQueryRecordList

class rDevice (rObject.rObject):
    def __init__(self, **kkw):
        rObject.rObject.__init__(self, table="device", **kkw)        
        self._roles = GenericQueryRecordList ()
        self._interfaces = GenericQueryRecordList ()        
        self._ipaddresses = GenericQueryRecordList ()        
        
    def reloadIpReservations(self):
        self._ipreservations.query = ("SELECT ip.* FROM {0}.ip_reservation ip INNER JOIN {0}.service s " +
            "ON ip.ownerid = s.objectid WHERE s.subscriberid = {1} ORDER BY ip.address").format (
                CFG.DB.SCHEMA, self.objectid )
        self._ipreservations.reload ( feed=True )

    def reloadInterfaces(self):
        self._interfaces.query = ("SELECT mac.* FROM {0}.mac_interface mac WHERE mac.deviceid = {1} ORDER BY mac.deviceid, mac.mac").format (
                CFG.DB.SCHEMA, self.objectid )
        self._interfaces.reload ( feed=True )    
    
    def getFirstIP(self):
        if not self.getExtraRecordData("first_ip"):
            self.setExtraRecordData("first_ip", CFG.CX.getcell ( "SELECT {0}.get_device_first_ip({1})".format (CFG.DB.SCHEMA, self.objectid) ))
        return self.getExtraRecordData("first_ip")        
        
    def _get_ipreservations(self):
        return self._ipreservations
    ipreservations = property(_get_ipreservations)

    def _get_interfaces(self):
        return self._interfaces
    interfaces = property(_get_interfaces)

    def _get_devices(self):
        return self._devices
    devices = property(_get_devices)

        
    