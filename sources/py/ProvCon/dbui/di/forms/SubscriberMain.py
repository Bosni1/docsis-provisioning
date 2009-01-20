from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin.forms import GenericForm
import wx
import wx.lib.scrolledpanel as scroll

class SubscriberMain(scroll.ScrolledPanel):
    
    def __init__(self, parent, *args):
        scroll.ScrolledPanel.__init__(self, parent, *args)
        
        self.form = AttrDict()
        self.table = AttrDict()
        self.editor = AttrDict()
        
        self.table.subscriber = meta.Table.Get ( "subscriber" )
        self.form.subscriber = orm.Form ( self.table.subscriber  )
        
        sizer_v1 = wx.BoxSizer (wx.VERTICAL)
        
        self.editor.subscriber  = GenericForm ( self.form.subscriber, self)
        self.editor.subscriber.create_widget()
        
        sizer_v1.Add ( wx.StaticText(self, label="NAVIGATION CONTROLS") )
        
        sizer_h2 = wx.BoxSizer (wx.HORIZONTAL)
        sizer_v1.Add ( sizer_h2, 10, wx.EXPAND )
        
        sizer_v3 = wx.BoxSizer(wx.VERTICAL)
        
        sizer_h2.Add ( wx.StaticText(self, label="TOOLBOX") )
        sizer_h2.Add ( sizer_v3,10, wx.EXPAND) 
        
        sizer_v3.Add ( wx.StaticText(self, label="INFO", size=wx.Size(-1,200)) )

        sizer_h4 = wx.BoxSizer (wx.HORIZONTAL)

        sizer_v3.Add ( sizer_h4, 2, wx.EXPAND )

        sizer_v5 = wx.BoxSizer (wx.VERTICAL)
        sizer_v6 = wx.BoxSizer (wx.VERTICAL)
        
        sizer_h4.Add ( sizer_v5, 2, wx.EXPAND )
        sizer_h4.Add ( sizer_v6, 2, wx.EXPAND )
                
        sizer_v5.Add ( self.editor.subscriber, 1, wx.EXPAND  )
        sizer_v5.Add ( wx.StaticText ( self, label="Lista uslug"), 2, wx.EXPAND )
        
        sizer_v6.Add ( wx.StaticText ( self, label="URZ. IP. MAC / Notes"), 1, wx.EXPAND )
        

        
        
        self.SetSizer(sizer_v1)
        
        
        
        
        
        
        