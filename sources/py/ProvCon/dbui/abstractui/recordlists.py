from ProvCon.func.events import eventemitter

class BaseRecordList(eventemitter):
    def __init__(self, records, *args, **kwargs):
        eventemitter.__init__ (self, [ "record_list_changed", "current_record_changed", "navigate" ] )
        self.__current_record = None
        self.set_records ( records )
        
    def set_records(self, records):
        self.records = records
        self.records_count = len(records)
        self.current_record = None
        self.emit_event ( "record_list_changed", self.get_records )

    def set_current_record (self, record):        
        self.__current_record = record
        self.emit_event ( "current_record_changed", self.__current_record )
    def get_current_record (self):
        return self.__current_record
    current_record = property (get_current_record, set_current_record)
        
    def get_records(self):
        return self.records
    
class BasePager(BaseRecordList):
    def __init__(self, records, pagesize, **kkw):                
        self.pagesize = pagesize
        
        BaseRecordList.__init__ (self, records, **kkw )
        self.add_emitted_event ( "page" )
        
        self.current_page = None
        self.page_count = None
        self.current_record_set = []
        self.set_page(1)
        self.get_records = self.current_record_set
    
    def set_records (self, records):
        BaseRecordList.set_records(self, records)
        self.page_count = self.record_count / self.pagesize
        self.set_page (1)
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
        