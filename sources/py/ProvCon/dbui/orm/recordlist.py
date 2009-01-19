##$Id$
from ProvCon.dbui.API import Implements, IRecordList
from ProvCon.func import eventemitter

__revision__ = "$Revision$"

@Implements(IRecordList)
class RecordList(list, eventemitter):
    """
    A simple list of database records.       
    """
    def __init__(self, table, _filter="TRUE", select=['0'], order="objectid", **kkw):
        list.__init__(self)
        eventemitter.__init__(self, [ "record_list_reloaded", 
                                      "record_list_item_reloaded",
                                      "record_list_changed"] )
        self.table = table
        self.filter = _filter
        self.select = select
        self.order = order
        self.recordclass = kkw.get ("recordclass", None)
        self.filterfunc = kkw.get("filterfunc", lambda r: True)
        self.hash_id = {}
        self.hash_index = {}
    
    def reload(self):
        """
        Re-query the database and refresh the list.
        """
        list.__init__(self)
        self += filter(self.filterfunc, self.table.recordObjectList (self.filter, self.select, self.order, self.recordclass))
        self.hash_id.clear()
        self.hash_index.clear()
        for idx, r in enumerate(self): 
            self.hash_id[r.objectid] = r
            self.hash_index[r.objectid] = idx
        self.emit_event ( "record_list_reloaded", self )
        self.emit_event ( "record_list_changed", self )
        return self
    
    def reloadsingle(self, objectid):
        """
        Refresh one record with given objectid.
        @type objectid: int
        """
        rl = self.table.recordObjectList ( self.filter + " AND o.objectid = %d " % objectid, self.select, self.order,self.recordclass)
        self[self.hash_index[objectid]] = rl[0]
        self.emit_event ( "record_list_item_reloaded", self.hash_index[objectid] )
        self.emit_event ( "record_list_changed", self )
            
    def clear(self):
        """
        Clear all records in the database.
        """
        list.__init__(self)
        self.hash_id.clear()
        self.emit_event ( "record_list_changed", self )
        
    def getindex(self, objectid):
        """
        Get the index of the record with the given objectid in the list. 
        Raise KeyError if not found.        
        """
        return self.hash_index[objectid]

    def getbyid(self, objectid):
        """Get an object from the list."""
        return self.hash_id[objectid]
