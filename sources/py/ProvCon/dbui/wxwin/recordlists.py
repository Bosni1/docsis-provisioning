from ProvCon.dbui.abstractui.recordlists import BaseRecordList
import wx, sys, wx.combo

class RecordList(BaseRecordList, wx.HtmlListBox):
    def __init__(self, records, parent, *args, **kwargs):
        BaseRecordList.__init__ (self, records, **kwargs)
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        wx.HtmlListBox.__init__ (self, parent,
                              style=wx.LC_NO_HEADER | wx.LC_REPORT | wx.LC_SINGLE_SEL     
                              )        
                
        self.listenForEvent ( "record_list_changed", self.populate_list )
        self.Bind ( wx.EVT_LISTBOX, self.item_selected )        
        #self.SetSelectionBackground (wx.Color(,40,40))        
        
    def OnGetItem(self, n):
        return self.reprfunc(self.records[n])    
        
    def item_selected(self, event, *args):
        self.current_record = self.records[event.GetInt()]
        #assert isinstance(event, wx.CommandEvent)
                
    def populate_list(self, *args):
        self.SetItemCount ( len(self.records) )
        #if len(self.records)>0:
        #    self.SetSelection(0)
        self.Refresh()
    
    def set_menu(self, menu):
        self.Bind ( wx.EVT_CONTEXT_MENU, self.on_menu )
        self.context_menu = menu
    
    def on_menu(self, evt, *args):
        self.context_menu.prepare()
        self.PopupMenu ( self.context_menu )
    
class RecordListMenu(wx.Menu):
    def __init__(self, recordlist, **kw):
        wx.Menu.__init__(self, **kw)
        self.recordlist = recordlist
        self.unformatted = {}
        
    def AddItem (self, name, fmt):
        newid = wx.NewId()
        item = self.Append (newid, text=fmt)        
        self.unformatted[name] = (item, fmt)
        if hasattr (self, "on_" + name):
            self.recordlist.Bind (wx.EVT_MENU, getattr(self, "on_" + name), id = newid )
            
    
    def prepare(self):
        if 0: assert isinstance(item, wx.MenuItem)
        currentrecord = self.recordlist.currentrecord
        for name in self.unformatted:
            item, fmt = self.unformatted[name]
            if currentrecord:
                txt = fmt.format ( currentrecord )
            else:
                txt = fmt
            item.SetText ( txt )
            
        
#class RecordListSelector(BaseRecordList, wx.