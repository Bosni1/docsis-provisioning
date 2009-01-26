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
import wx.lib.buttonpanel as bp

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
        p = bp.ButtonPanel (self, 
    
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
        
        ###
        ###   INFO PANEL (static data)  
        ###        
        self.info_panel = SubscriberInfoPanel(self, self.form.subscriber)

        #############################################################################
        
        def _format_service(r):
            return r.typeofservice_REF + "\n" + r.classofservice_REF

        self.recordlist.services = rl.RecordList(self.store.services, self,
                                                 reprfunc = _format_service)
        self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber)


        self.mgr.AddPane ( self.info_panel, wx.aui.AuiPaneInfo().Top().
                           Floatable(False).CloseButton(False).
                           Name("subscriber_info").
                           Caption("Klient").                           
                           MinSize( (-1, 200) )
                           )
        self.mgr.AddPane ( subscroll, wx.aui.AuiPaneInfo().Center().
                           Floatable(False).CloseButton(False).
                           Name("subscriber_editor").
                           Caption("Podstawowe dane klienta").
                           Position(0).
                           MinSize( (-1, 300) )
                           )        
        self.mgr.AddPane ( self.recordlist.services, wx.aui.AuiPaneInfo().Center().
                           Floatable(False).CloseButton(False).
                           Name("service_list").
                           Position(1).
                           Caption("Usługi")
                        )
                           

        self.mgr.Update()

        
        self.form.subscriber.setid ( self.store.subscriber[0].objectid )
        
        
        
        
        
        
        