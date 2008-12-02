from ProvCon.func import eventemitter, eventcancelled
        

class BaseNavigator(eventemitter):
    def __init__(self, *args, **kwargs):
        """
        required keyword args:
         records : list of records (instance of RecordList)
         oidname : name of the record field which serves 
         displayname : name of the record field which holds the displayed value
        """
        eventemitter.__init__ (self, [ "navigate" ] )
        self.index_id_hash = {}
        self.records_count = 0
        self.records = []
        self.set_records (kwargs.get ( "records", [] ), **kwargs)
        self.oidname = kwargs.get ( "oidname", "objectid" )
        self.displayname = kwargs.get ( "displayname", "_astxt" )
        self.current_index = kwargs.get ( "current_index", None )
        self.previous_index = None
        
        #self.first()        
    
    def update(self):
        raise NotImplementedError()
    
    def set_records(self, records):
        self.records = records
        self.records_count = len(self.records)
        self.current_index = None
        self.index_id_hash.clear()
        for idx, r in enumerate(self.records):
            self.index_id_hash[r[self.oidname]] = idx
        
    def currentid(self):
        try:
            return self.records[self.current_index][self.oidname]
        except TypeError:
            return None
        except IndexError:
            return None
    
    def currentdisplay(self):
        if self.current_index == "NEW_RECORD":
            return "NEW RECORD"
        try:
            return self.records[self.current_index][self.displayname]
        except IndexError:        
            return ''
        except KeyError:
            return str(self.records[self.current_index])

    def indexof (self, oid):
        return self.index_id_hash.get ( oid, None )
    
    def on_new_record (self):
        pass
    
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
            
    def navigate(self, new_idx):
        if new_idx == "NEW_RECORD":
            self.on_new_record ()            
        
        self.previous_index = self.current_index
        self.current_index = new_idx
        
        try:
            self.update()
            self.emit_event ( "navigate", self.currentid())
        except eventcancelled:
            self.current_index = self.previous_index
            self.update()
            
        return self.current_index
    
        
    def navigate_relative (self, delta):        
        try:
            return self.navigate ( (self.current_index + delta) % self.records_count )
        except ZeroDivisionError:
            return self.navigate ( None )
        except TypeError:
            if self.current_index == "NEW_RECORD":                            
                if self.previous_index:
                    self.navigate ( self.previous_index )                
                else:
                    self.navigate ( self.records_count - 1)
            else:
                raise
            
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
        

        
        
        