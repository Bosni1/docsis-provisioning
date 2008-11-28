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
    
    
        
class BasePager(eventemitter):
    def __init__(self, records, pagesize, **kkw):
        eventemitter.__init__ (self, [ "page" ] )
        self.records = records
        self.pagesize = pagesize
        self.current_page = None
        self.page_count = None
        self.current_record_set = []
        self.set_page(1)
    
    def set_records (self, records):
        self.records = records
        self.record_count = len(records)
        self.page_count = self.record_count / self.pagesize
        if self.record_count % self.pagesize > 0: self.page_count += 1

    def get_current_page ( self ):
        return self.current_record_set
    
    def set_page(self, pageno):
        if pageno < 0 or pageno >= self.page_count: return
        self.current_page = pageno
        self.current_record_set = self.records[pageno*self.pagesize:][:self.pagesize]
        self.emit_event ( "page", pageno, self.current_record_set )

    def page_relative(self, move):
        self.set_page ( (self.current_page + move) % self.page_count )
        
    def pageup(self): 
        self.page_relative ( 1 )
        
    def pagedown(self):
        self.page_relative ( -1 )
    
    def pagelast(self):
        self.page (self.page_count-1)
    
    def pagefirst(self):
        self.page (0)
        
        
        