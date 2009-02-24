import rObject
from ProvCon.dbui.database import CFG
from ProvCon.dbui.orm import GenericQueryRecordList

class rSubscriber (rObject.rObject):
    def __init__(self, **kkw):
        rObject.rObject.__init__(self, table="subscriber", **kkw)
        self._ipreservations = GenericQueryRecordList ()
        self._macaddresses = GenericQueryRecordList ()
        self._devices = GenericQueryRecordList ()
        
    def reloadIpReservations(self):
        self._ipreservations.query = ("SELECT ip.* FROM {0}.ip_reservation ip INNER JOIN {0}.service s " +
            "ON ip.ownerid = s.objectid WHERE s.subscriberid = {1} ORDER BY ip.address").format (
                CFG.DB.SCHEMA, self.objectid )
        self._ipreservations.reload ( feed=True )

    def reloadMACAddresses(self):
        self._macaddresses.query = ("SELECT mac.* FROM {0}.mac_interface mac INNER JOIN {0}.service s " +
            "ON mac.ownerid = s.objectid WHERE s.subscriberid = {1} ORDER BY mac.mac").format (
                CFG.DB.SCHEMA, self.objectid )
        self._macaddresses.reload ( feed=True )

    def reloadDevices(self):
        self._devices.query = ("SELECT dev.* FROM {0}.service s INNER JOIN {0}._mtm_service_device mtm " +
            " ON mtm.serviceid = s.objectid INNER JOIN {0}.device dev ON mtm.deviceid = dev.objectid " +
            " WHERE s.subscriberid= {1} ").format (
                CFG.DB.SCHEMA, self.objectid )
        self._devices.reload ( feed=True )
        
    def _get_ipreservations(self):
        return self._ipreservations
    ipreservations = property(_get_ipreservations)

    def _get_macaddresses(self):
        return self._macaddresses
    macaddresses = property(_get_macaddresses)

    def _get_devices(self):
        return self._devices
    devices = property(_get_devices)

        
    