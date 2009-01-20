from ProvCon.dbui.abstractui.recordlists import BaseRecordList
import wx, sys

class RecordList(BaseRecordList, wx.HtmlListBox):
    def __init__(self, records, parent, *args, **kwargs):
        BaseRecordList.__init__ (self, records, **kwargs)
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        wx.HtmlListBox.__init__ (self, parent,
                              style=wx.LC_NO_HEADER | wx.LC_REPORT | wx.LC_SINGLE_SEL     
                              )        
                
        self.register_event_hook ( "record_list_changed", self.populate_list )
        self.Bind ( wx.EVT_LISTBOX, self.item_selected )        
        self.SetSelectionBackground (wx.Color(40,40,40))        
    def OnGetItem(self, n):
        return self.reprfunc(self.records[n])
        
    def item_selected(self, event, *args):
        self.current_record = self.records[event.GetInt()]
        #assert isinstance(event, wx.CommandEvent)
                
    def populate_list(self, *args):
        self.SetItemCount ( len(self.records) )
        if len(self.records)>0:
            self.SetSelection(0)
        self.Refresh()
    
                                                        