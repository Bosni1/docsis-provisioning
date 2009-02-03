# -*- coding: utf8 -*-
from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin.forms import GenericForm, ScrolledGenericForm
from ProvCon.dbui.wxwin import recordlists as rl
from ProvCon.dbui.wxwin.fields import Entry
import wx
import wx.aui
import wx.lib.scrolledpanel as scroll
import wx.lib.rcsizer as rcs

class SubscriberInfoPanel(wx.Panel):
    
    def __init__(self, parent, form, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.form = form
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        font18 = wx.Font (18, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        font20 = wx.Font (20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        font20b = wx.Font (20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font22b = wx.Font (22, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        self.edit = AttrDict()
        self.edit.subscriberid = Entry.Static ( self.form.table["subscriberid"], self, variable = self.form.getvar("subscriberid" ) )
        self.edit.name = Entry.Static ( self.form.table["name"], self, variable = self.form.getvar("name" ) )
        self.edit.primarylocation = Entry.StaticReference ( self.form.table["primarylocationid"], self, variable = self.form.getvar("primarylocationid" ) )
        
        for ctrl in self.edit.values():            
            ctrl.SetForegroundColour (wx.Color(0,0,0))
            ctrl.SetFont ( font18 )                
        self.edit.subscriberid.SetFont ( font22b )
        
        self.row_1 = rcs.RowColSizer()
        self.row_1.Add ( self.edit.subscriberid, row=1, col=1, rowspan=2, border=30, flag=wx.ALIGN_CENTER | wx.RIGHT )
        self.row_1.Add ( self.edit.name, row=1,col=2, flag=wx.EXPAND)
        self.row_1.Add ( self.edit.primarylocation, row=2,col=2, flag=wx.EXPAND)

        self.sizer.Add (self.row_1)

        
        
        self.SetSizer (self.sizer)
        



class SubscriberCommandPanel(wx.Panel):
    def __init__(self, parent, form, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        sizer = wx.BoxSizer (wx.VERTICAL)
        
        self.form = form

        for i in range(14):
            sizer.Add ( wx.Button (self, label="TOOL%d" % i, style=wx.NO_BORDER),1, flag=wx.EXPAND)
        
        self.SetSizer(sizer)
    
class SubscriberMain(wx.Panel):
    
    def __init__(self, parent, *args):
        wx.Panel.__init__(self, parent, *args)
        
        self.form = AttrDict()
        self.table = AttrDict()
        self.editor = AttrDict()
        self.store = AttrDict()
        self.recordlist = AttrDict()
        
        self.table.subscriber = meta.Table.Get ( "subscriber" )
        self.table.service = meta.Table.Get ( "service" )
        

        self.store.subscriber = orm.RecordList ( self.table.subscriber ).reload()
        self.store.services = orm.RecordList ( self.table.service, select=["classofservice","typeofservice","handle"] )
        self.form.subscriber = orm.Form ( self.table.subscriber  )

        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow (self)
        
        subscroll = ScrolledGenericForm(self.form.subscriber, self)
        self.editor.subscriber = subscroll.genericform                        
        
        self.info_panel = SubscriberInfoPanel(self, self.form.subscriber)
        self.command_panel = SubscriberCommandPanel(self, self.form.subscriber)

        self.tb = wx.ToolBar (self)
        self.tb.SetToolBitmapSize ( wx.Size(48,48) )
        i = self.tb.AddLabelTool ( wx.NewId(), "Nowy rekord", wx.ArtProvider_GetBitmap(wx.ART_NEW) )
        i = self.tb.AddLabelTool ( wx.NewId(), "Zapisz", wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE) )
        self.tb.Realize()
        
        def _format_service(r):
            return r.typeofservice_REF + "\n" + r.classofservice_REF

        self.recordlist.services = rl.RecordList(self.store.services, self,
                                                 reprfunc = _format_service)
        self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber)

        
        self.mgr.AddPane ( self.info_panel, wx.aui.AuiPaneInfo().Top().
                           Floatable(False).CloseButton(False).
                           Caption("Podsumowanie danych klienta").
                           Name("info_panel").
                           Layer(1).
                           MinSize( (-1, 170) ).
                           BestSize( (700,170) )
                           )
        self.mgr.AddPane ( wx.Panel(self), wx.aui.AuiPaneInfo().Bottom().
                           Floatable(True).CloseButton(True).Float().Dockable(False).Hide().
                           Name("search_results").
                           Caption("Wyniki wyszukiwania...").
                           Layer(1).
                           MinSize( ( 300, 250) )
                           )

        self.mgr.AddPane ( subscroll, wx.aui.AuiPaneInfo().CentrePane().
                           Floatable(False).CloseButton(False).
                           Name("subscriber_editor").
                           Layer(0)                           
                           )        
        
        self.mgr.AddPane ( self.recordlist.services, wx.aui.AuiPaneInfo().Bottom().
                           Floatable(False).CloseButton(False).
                           Name("service_list").                           
                           Layer(0).
                           Row(1).
                           Caption("Usługi").
                           MinSize( (-1, 120) )
                        )
        self.mgr.AddPane ( wx.Panel(self), wx.aui.AuiPaneInfo().Bottom().
                           Floatable(False).CloseButton(False).
                           Name("device_list").                           
                           Layer(0).
                           Row(0).
                           Caption("Urządzenia").
                           MinSize( (-1, 160) )
                        )

        self.mgr.AddPane ( self.command_panel, wx.aui.AuiPaneInfo().Left().
                           Floatable(False).CloseButton(False).
                           Name("command_panel").Caption("Toolbox").
                           Layer(1).
                           MinSize((100,-1))
                           )
        
        self.mgr.AddPane ( wx.Panel(self), wx.aui.AuiPaneInfo().Right().
                           CloseButton(False).
                           Name("ip_address_list").Caption("Adresy IP").
                           Layer(1).                           
                           MinSize( (300,-1) )                           
                           )
        self.mgr.AddPane ( wx.Panel(self), wx.aui.AuiPaneInfo().Right().
                           CloseButton(False).
                           Name("mac_address_list").Caption("MAC").
                           Layer(1).
                           MinSize( (300,-1) )                           
                           )
        self.mgr.AddPane ( self.tb, wx.aui.AuiPaneInfo().Name("record_toolbar").
                           ToolbarPane().Top().Layer(2)
                           )
        self.mgr.Update()

        
        self.form.subscriber.setid ( self.store.subscriber[10].objectid )
        #self.form.subscriber.new()
        
        
        
        
        
        
        