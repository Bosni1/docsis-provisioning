from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin.forms import GenericForm, ScrolledGenericForm
from ProvCon.dbui.wxwin import recordlists as rl
import wx
import wx.lib.scrolledpanel as scroll

class SubscriberMain(scroll.ScrolledPanel):
    
    def __init__(self, parent, *args):
        scroll.ScrolledPanel.__init__(self, parent, *args)
        
        self.form = AttrDict()
        self.table = AttrDict()
        self.editor = AttrDict()
        self.store = AttrDict()
        self.recordlist = AttrDict()
        
        self.table.subscriber = meta.Table.Get ( "subscriber" )
        self.table.service = meta.Table.Get ( "service" )
        

        self.store.subscriber = orm.RecordList ( self.table.subscriber ).reload()
        self.store.services = orm.RecordList ( self.table.service )
        self.form.subscriber = orm.Form ( self.table.subscriber  )
        
        sizer_v1 = wx.BoxSizer (wx.VERTICAL)                    
        
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
        
        
        subscroll = ScrolledGenericForm(self.form.subscriber, self)
        self.editor.subscriber = subscroll.genericform                
        
        sizer_v5.Add ( subscroll, 2, wx.EXPAND  )

        self.recordlist.services = rl.RecordList(self.store.services, self)                                                     
        self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber )
        
        sizer_v5.Add ( self.recordlist.services, 1, wx.EXPAND )
        
        sizer_v6.Add ( wx.StaticText ( self, label="URZ. IP. MAC / Notes"), 1, wx.EXPAND )
        
        self.form.subscriber.setid ( self.store.subscriber[0].objectid )
        
        self.SetSizer(sizer_v1)
        self.SetAutoLayout(1)

        
        
        
        
        
        