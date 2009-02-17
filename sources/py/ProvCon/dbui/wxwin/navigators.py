from ProvCon.dbui.abstractui.navigators import BaseNavigator
from recordlists import RecordList
from ProvCon.dbui import orm
from app import APP
from mwx import RecordListCombo
import wx

class Navigator(BaseNavigator, wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        BaseNavigator.__init__ ( self, *args, **kwargs )
        wx.Panel.__init__ ( self, parent )
        self.sizer = wx.BoxSizer ( wx.HORIZONTAL )

        button_opt = { 'style' : wx.BU_EXACTFIT }
        elements = []
        
        labels = {}
        for bname in ["first", "prev", "next", "last", "search"]:
            elements.append ( wx.Button ( self, label=labels.get(bname, bname), name=bname, **button_opt ) )
            
        for b in elements:
            b.SetFont (wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))            
            b.Bind ( wx.EVT_BUTTON,getattr(self, b.Name) )
        
        #txt = wx.TextCtrl (self)
        #txt.SetFont ( wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD) )
        #txt.SetForegroundColour ( wx.NamedColor ( "blue" ) )
        #txt.SetBackgroundColour ( wx.NamedColor ( "yellow") )
        #txt.SetEditable(False)
        
        #self.infotext = txt
        self.nav = RecordListCombo (self, self.records)
        self.navhook = self.nav.listenForEvent ( "current_record_changed", self.nav_changed )
        
        label = wx.StaticText (self)
        label.SetFont ( wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD) )
        label.ForegroundColour = (0,0,0)
        self.label = label
        
        self.sizer.Add ( elements[0], 0 )
        self.sizer.Add ( elements[1], 0 )
        self.sizer.Add ( self.nav, 10, flag=wx.EXPAND )
        self.sizer.Add ( label, 2, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER, border = 4 ) 
        self.sizer.Add ( elements[2], 0 )
        self.sizer.Add ( elements[3], 0 )
        self.sizer.Add ( elements[4], 0 )
        
        self.SetSizer (self.sizer)
    
    def update(self):
        #self.infotext.SetValue ( self.currentdisplay() )
        if not self.isonnew():
            self.label.SetLabel ( " %5d / %d " % (self.current_index+1, self.records_count) ) 
            self.nav.set_oid ( self.currentid() )
        else:
            self.label.SetLabel ( " %5d / %d " % (self.records_count+1, self.records_count) ) 
            self.nav.set_null()
    
    def search(self, *args):
        pass
    
    def search_results(self, results):
        pass
    
    def nav_changed(self, record, *args):
        self.setid ( record.objectid )