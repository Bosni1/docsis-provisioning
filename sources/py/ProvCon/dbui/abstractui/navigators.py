from ProvCon.func import eventemitter, eventcancelled
from gettext import gettext as _        
from ProvCon.dbui.API import *

__revision__ = "$Revision$"

@Implements(INavigator)
class BaseNavigator(eventemitter):
    def __init__(self, *args, **kwargs):
        """
        BaseNavigator ( 
   keywords: records : IRecordList (required), 
             oidname : str = 'objectid',
             displayname : str = '_astxt',
             current_index : int = None,             
         )           
        """
        eventemitter.__init__ (self, [ "navigate" ] )
        
        self.index_id_hash = {}        
        self.records_count = 0
        self.__records = None
        self.records =  kwargs.get ( "records", [] )
        
        self.oidname = kwargs.get ( "oidname", "objectid" )
        self.displayname = kwargs.get ( "displayname", "_astxt" )
        self.current_index = kwargs.get ( "current_index", None )
        self.previous_index = None
        self.new_record = False
    
    def update(self):
        """
        Called when items in the recordlist are changed. Refreshes anything that
        needs to be refreshed.
        """
        raise NotImplementedError()
    
    def set_records(self, records):
        self.__records = records
        self.records_count = len(self.records)
        self.current_index = None
        self.new_record = False
        self.index_id_hash.clear()
        for idx, r in enumerate(self.records):
            self.index_id_hash[r[self.oidname]] = idx
            
    def get_records(self):
        return self.__records
    records = property(get_records, set_records)
    """ records : IRecordList """
    
    def currentid(self):
        if self.isonnew(): return None
        try:
            return self.records[self.current_index][self.oidname]
        except TypeError:
            return None
        except IndexError:
            return None

    def currentrecord(self):
        if self.currentid():
            return self.records.getbyid (self.currentid())
        return None
    
    def setid(self, objectid):
        self.navigate ( self.indexof ( objectid ) )
        
    def isonnew(self):
        return self.new_record
    
    def currentdisplay(self):
        if self.isonnew():
            return "** " + _("NEW RECORD") + " **"
        try:
            return self.records[self.current_index][self.displayname]
        except IndexError:        
            return ''
        except KeyError:
            return str(self.records[self.current_index])

    def indexof (self, oid):
        return self.index_id_hash.get ( oid, None )
        
    def reload(self, movetoid=None):        
        self.set_records ( self.records.reload () )
        if movetoid==-1:
            self.navigate (0)
        elif movetoid:
            self.navigate ( self.indexof ( movetoid) )
            
        self.update()
        
    def reloadsingle (self, objectid):
        self.records.reloadsingle ( objectid )
        self.update ()
            
    def navigate(self, new_idx, newrecord=True):
        
        self.previous_index = self.current_index
        self.current_index = new_idx
        if self.current_index is None and newrecord:
            self.new_record = True
        else:
            self.new_record = False
        
        try:
            self.update()
            self.emit_event ( "navigate", self.currentid())
        except eventcancelled:
            self.current_index = self.previous_index
            self.update()
            
        return self.current_index
    
        
    def navigate_relative (self, delta):        
        try:
            if self.isonnew(): 
                if self.previous_index:
                    return self.navigate ( self.previous_index )                
                else:
                    return self.navigate ( self.records_count - 1)
            else:
                return self.navigate ( (self.current_index + delta) % self.records_count )
        except ZeroDivisionError:
            return self.navigate ( None )
            
    def next(self, *args): 
        return self.navigate_relative(1)
    
    def prev(self, *args): 
        return self.navigate_relative(-1)
    
    def first(self,*args): 
        return self.navigate (0)
    
    def last(self,*args): 
        return self.navigate(self.records_count-1)
    
    def __len__(self):
        return self.records_count
        

        
        
        