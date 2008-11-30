from ProvCon.func import eventemitter, eventcancelled
        

class BaseNavigator(eventemitter):
    def __init__(self, *args, **kwargs):
        """
        required keyword args:
         records : list of records
         oidname : name of the record field which serves 
         displayname : name of the record field which holds the displayed value
        """
        eventemitter.__init__ (self, [ "navigate" ] )
        self.records_count = 0
        self.records = []
        self.set_records (kwargs.get ( "records", [] ), **kwargs)
        self.oidname = kwargs.get ( "oidname", "objectid" )
        self.displayname = kwargs.get ( "displayname", "_astxt" )
        self.current_index = kwargs.get ( "current_index", None )
        #self.first()        
    
    def update(self):
        raise NotImplementedError()
    
    def set_records(self, records):
        self.records = records
        self.records_count = len(self.records)
        self.current_index = None
        
    def currentid(self):
        try:
            return self.records[self.current_index][self.oidname]
        except IndexError:
            return None
        
    def currentdisplay(self):
        try:
            return self.records[self.current_index][self.displayname]
        except IndexError:        
            return ''
        except KeyError:
            return str(self.records[self.current_index])
        
    def navigate(self, new_idx):
        oldidx = self.current_index
        self.current_index = new_idx
        
        try:
            self.update()
            self.emit_event ( "navigate", self.currentid())
        except eventcancelled:
            self.current_index = oldidx
            self.update()
            
        return self.current_index
    
        
    def navigate_relative (self, delta):        
        try:
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
    
    
        

        
        
        