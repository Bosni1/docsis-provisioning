from ProvCon.func import eventemitter

class BaseNavigator(eventemitter):
    def __init__(self, *args, **kwargs):
        self.set_records (kwargs.get ( "records", [] ), **kwargs)

    def set_records(self, records, **kwargs):
        self.records = records
        self.oidname = kwargs.get ( "oidname", "objectid" )
        self.displayname = kwargs.get ( "displayname", "_astxt" )
        self.current_index = kwargs.get ( "current_index", None )
        
    def currentid(self):
        try:
            return self.records[self.current_index][self.oidname]
        except IndexError:
            return None
        
    def currentdisplay(self):
        try:
            return self.records[self.current_index][self.displayname]
        except IndexError:        
            return None
        except KeyError:
            return str(self.records[self.current_index])
        
    def navigate(self, new_idx):
        self.current_index = new_idx
        self.emit_event ( "navigate", self.currentid())
        
    def navigate_relative (self, delta):
        new_idx = self.current_index + delta
        if new_idx >= len(self.records):
            new_idx 
