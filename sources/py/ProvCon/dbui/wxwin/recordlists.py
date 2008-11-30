from ProvCon.dbui.abstractui.recordlists import BaseRecordList
import wx, sys

class RecordList(BaseRecordList, wx.ListCtrl):
    def __init__(self, records, parent, *args, **kwargs):
        BaseRecordList.__init__ (self, records)
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        wx.ListCtrl.__init__ (self, parent,
                              style=wx.LC_NO_HEADER | wx.LC_REPORT      
                              )
        self.InsertColumn (0, "text")        
        
        self.register_event_hook ( "record_list_changed", self.populate_list )
        self.Bind ( wx.EVT_LIST_ITEM_SELECTED, self.item_selected )

    def item_selected(self, event, *args):
        self.emit_event( "navigate", event.GetData() )
        self.current_record = self.records.getid(event.GetData())        
                
    def populate_list(self, *args):
        self.DeleteAllItems()
        for r in self.get_records():            
            index = self.InsertStringItem ( sys.maxint, self.reprfunc(r) )
            self.SetItemData ( index, r.objectid )
        self.SetColumnWidth (0, wx.LIST_AUTOSIZE )
    