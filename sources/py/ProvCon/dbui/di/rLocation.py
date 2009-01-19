import rObject
from ProvCon.dbui.database import CFG

class rLocation (rObject.rObject):
    def __init__(self, **kkw):
        rObject.rObject.__init__(self, table="location", **kkw)
        self._generic_handle = None
        
        
    def getGenericHandle(self, reload=True):
        if reload:
            self._generic_handle = CFG.CX.query ( 
                "SELECT {0}.location_generic_handle({1}) as handle;".format (
                    CFG.CX.schemaname, self.objectid) 
            ).dictresult()[0]["handle"]
        return self._generic_handle
        