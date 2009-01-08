## $Id$
from ProvCon.func.events import eventemitter, eventcancelled
"""
RecordList widgets hold a list of records.
It is important to distinguish between record list widgets (which implement 
the IRecordListHolder interface), and record lists ( IRecordList )
"""
from ProvCon.dbui.API import Implements, IRecordListHolder, INavigator

__revision__ = "$Revision$"
 
@Implements(IRecordListHolder)
class BaseRecordList(eventemitter):
    def __init__(self, records, *args, **kwargs):
        """ BaseRecordList ( records : IRecordList ) """
        eventemitter.__init__ (self, [ "record_list_changed", 
                                       "current_record_changed", 
                                       "navigate" ] )
        self.__current_record = None
        self.__records = None
        self.set_records ( records )
        
        boundform = kwargs.get ( "boundform", None )        
        boundfield = kwargs.get( "boundfield", None )        
        self.parentform = None
        if boundfield and boundform:
            self.bind_to_form ( boundfield, boundform )
        
    def set_records(self, records):
        self.__records = records
        self.records_count = len(self.__records)
        self.current_record = None
        self.emit_event ( "record_list_changed", self.get_records() )

    def get_records(self):
        return self.__records
    records = property (get_records, set_records)

    def currentid(self):
        if self.current_record:
            return self.current_record._objectid
        else:
            return None

    def currentdisplay(self):        
        return str(self.current_record)
        
    def set_current_record (self, record):            
        oldrecord = self.current_record        
        try: 
            self.__current_record = record
            self.emit_event ( "navigate", self.currentid() )
            self.emit_event ( "current_record_changed", self.__current_record )            
        except eventcancelled:
            self.__current_record = oldrecord
    
            
    def get_current_record (self):
        return self.__current_record
    current_record = property (get_current_record, set_current_record)
    currentrecord = current_record

    
    def bind_to_form (self, myfield, form):
        self.parentform = (form, myfield)        
        self.parenthook = form.register_event_hook ( "current_record_changed", self._on_parent_record_changed)            
        
    def _on_parent_record_changed(self, parentrecord):
        if parentrecord and parentrecord._objectid:
            (pform, myfield) = self.parentform        
            self.records.filter = '"{0}" = \'{1}\''.format ( myfield, parentrecord.objectid )
            self.records.reload()            
        else:
            self.records.clear()
            self.records.filter = ' FALSE '
        self.set_records ( self.records )
    
    def isonnew(self, *args):
        return False
    
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

## $Author$
