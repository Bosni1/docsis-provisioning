from ProvCon.func import eventemitter

class BaseNavigator(eventemitter):
    def __init__(self, *args, **kwargs):
        self.records = kwargs.get ( "records", [] )
        self.oidname = kwargs.get ( "oidname", "objectid" )
        self.displayname = kwargs.get ( "displayname", "_astxt" )
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
            return None
        
        
