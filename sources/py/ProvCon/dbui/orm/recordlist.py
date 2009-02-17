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
        self.rehash()
        self.raiseEvent ( "record_list_reloaded", self )
        self.raiseEvent ( "record_list_changed", self )
        return self
    
    def rehash(self):
        self.hash_id.clear()
        self.hash_index.clear()
        for idx, r in enumerate(self): 
            self.hash_id[r.objectid] = r
            self.hash_index[r.objectid] = idx

    
    def reloadsingle(self, objectid):
        """
        Refresh one record with given objectid.
        If the record was not in the list, it is appended to it.
        
        @type objectid: int
        """
        try:
            rl = self.table.recordObjectList ( self.filter + " AND o.objectid = %d " % objectid, self.select, self.order,self.recordclass)[0]
        except KeyError:   #record not found
            return
        try:
            self[self.hash_index[objectid]] = rl            
        except KeyError:
            self.append (rl)
            self.hash_index[objectid] = len(self) - 1
            self.hash_id[objectid] = rl            
        finally:
            self.raiseEvent ( "record_list_item_reloaded", self.hash_index[objectid] )
            self.raiseEvent ( "record_list_changed", self )
            
    def clear(self):
        """
        Clear all records in the database.
        """
        list.__init__(self)
        self.hash_id.clear()
        self.hash_index.clear()
        self.raiseEvent ( "record_list_changed", self )
        
    def getindex(self, objectid):
        """
        Get the index of the record with the given objectid in the list. 
        Raise KeyError if not found.        
        """
        return self.hash_index[objectid]

    def getbyid(self, objectid):
        """Get an object from the list."""
        return self.hash_id[objectid]

@Implements(IRecordList)    
class RelatedRecordList(RecordList):
    def __init__(self, table, mtm_handle, **kw):
        RecordList.__init__ (self, table, **kw)
        self.parent_objectid = None

    def setParentObjectID(self, objectid):
        if objectid == self.parent_objectid: return
        self.parent_objectid = objectid
        if objectid is None: self.clear()
        else: self.reload()
    def getParentObjectID(self):
        return self.parent_objectid
    parentobjectid = property(getParentObjectID, setParentObjectID)
    def isbound(self):
        return self.parentobjectid is not None
    bound = property(isbound)
    
    def reload(self):        
        list.__init__(self)
        if not self.bound: return self
        
        self += filter( self.filterfunc, self.table.relatedRecordList ( self.parentobjectid, self.mtm_handle ) )
        self.rehash()
        self.raiseEvent ( "record_list_reloaded", self )
        self.raiseEvent ( "record_list_changed", self )
        return self
    
    def reloadsingle(self, objectid):
        if objectid in self.hash_index:
            return RecordList.reloadsingle(self, objectid)
        return None
    

class GenericQueryRecordList(RecordList):
    def __init__(self, query="SELECT NULL LIMIT 0", filters = [], recordclass=None):
        from ProvCon.dbui.orm import Record
        
        RecordList.__init__(self, None)
        self.filters = filters
        self.query = query
        self.recordclass = recordclass or Record        
        
    def reload(self, feed=False):
        from ProvCon.dbui.database import CFG        
        list.__init__(self)
        result = CFG.CX.query ( self.query.format ( " AND ".join (self.filters) ) ).dictresult()
        for row in result:
            rec = self.recordclass.EMPTY ( row ['objecttype'] )
            if feed:
                rec.feedDataRow (row)
            else:                
                rec.setObjectID ( row['objectid'] )
            self.append (rec)
            
        self.rehash()
        self.raiseEvent ( "record_list_reloaded", self )
        self.raiseEvent ( "record_list_changed", self )
        return self
    
    def reloadsingle(self, objectid):
        try:
            rec = self.getbyid(objectid)
            rec.read()
        except KeyError:
            rec = self.recordclass.ID (objectid)
            self.append (rec)
            self.rehash()
        finally:
            self.raiseEvent ( "record_list_item_reloaded", self.hash_index[objectid] )
            self.raiseEvent ( "record_list_changed", self )
        
@Implements(IRecordList)
class RecordListView(eventemitter):    
    def __init__(self, masterlist, predicate = lambda x: False):
        eventemitter.__init__(self, [ "record_list_reloaded", 
                                      "record_list_item_reloaded",
                                      "record_list_changed"] )
        self.master = masterlist
        self._predicate = None
        self.predicate = predicate
        self.cache = None
        self.ids_in_cache = None
        self.hash_index = None        
        self.hash_id = None
        
        self.reload_hook = self.master.listenForEvent ( "record_list_reloaded", self.master_reloaded )
        self.change_hook = self.master.listenForEvent ( "record_list_changed", self.master_changed )
        self.item_reload_hook = self.master.listenForEvent ( "record_list_item_reloaded", self.master_item_reloaded )
        
    def set_predicate(self, predicate):
        self._predicate = predicate
        self.clear()
    def get_predicate(self):
        return self._predicate
    predicate = property(get_predicate, set_predicate)

    def init_cache(self):
        self.cache = []
        self.ids_in_cache = []
        self.hash_index = {}
        self.hash_id = {}

        for idx, r in enumerate(self.master):
            if self._predicate(r): 
                self.cache.append (r)
                self.ids_in_cache.append (r.objectid)
                self.hash_id[r.objectid] = r
                self.hash_index[r.objectid] = idx
                
    def get_or_init_cache(self):
        if self.cache is None:
            self.init_cache()
        return self.cache
    
    def __len__(self):
        return len(self.get_or_init_cache())

    def __contains__(self, objectid):
        self.get_or_init_cache()
        return objectid in self.ids_in_cache
    
    def __iter__(self):
        return iter(self.get_or_init_cache())

    def __getitem__(self, key):
        return self.get_or_init_cache()[key]


    def master_changed(self, *args):
        self.clear()
        self.raiseEvent ( "record_list_changed", self )
    
    def master_reloaded(self, *args):
        self.clear()
        self.raiseEvent ( "record_list_reloaded", self )

    def master_item_reloaded(self, masteridx):
        if self.master[masteridx].objectid in self:
            self.clear()
            self.raiseEvent ( "record_list_reloaded", self)
        
    def getindex(self, objectid):
        self.get_or_init_cache()
        return self.hash_index[objectid]
    
    def getbyid(self, objectid):
        self.get_or_init_cache()
        return self.hash_id(objectid)
                               
    def clear(self, *args):
        self.cache = None
        self.raiseEvent ( "record_list_changed", self )
        
    def reload(self):
        if len(self.master) > 0:
            if len(self) < 100 or float(len(self)) / len(self.master) < 0.005:
                for r in enumerate:                    
                    self.master.reloadsingle ( r.objectid )
            else:
                self.master.reload()
            self.clear()
            self.get_or_init_cache()
            self.raiseEvent ( "record_list_reloaded", self )
            self.raiseEvent ( "record_list_changed", self )
    
    def reloadsingle(self, objectid):
        self.master.reloadsingle(objectid)
        
        
    