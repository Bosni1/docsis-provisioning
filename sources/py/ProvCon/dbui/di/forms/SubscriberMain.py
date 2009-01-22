# -*- coding: utf8 -*-
from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin.forms import GenericForm, ScrolledGenericForm
from ProvCon.dbui.wxwin import recordlists as rl
from ProvCon.dbui.wxwin.fields import Entry
import wx
import wx.aui
import wx.lib.scrolledpanel as scroll

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
        
        #subscroll = ScrolledGenericForm(self.form.subscriber, self)
        #self.editor.subscriber = subscroll.genericform                
        self.editor.subscriber = GenericForm (self.form.subscriber, self)
        self.editor.subscriber.create_widget()
        #sizer_v1 = wx.BoxSizer (wx.VERTICAL)                    
        
        #sizer_v1.Add ( wx.StaticText(self, label="NAVIGATION CONTROLS") )
        
        #sizer_h2 = wx.BoxSizer (wx.HORIZONTAL)
        #sizer_v1.Add ( sizer_h2, 10, wx.EXPAND )
        
        #sizer_v3 = wx.BoxSizer(wx.VERTICAL)
        
        #sizer_h2.Add ( wx.StaticText(self, label="TOOLBOX") )
        #sizer_h2.Add ( sizer_v3,10, wx.EXPAND) 
        
        ###
        ###   INFO PANEL (static data)  
        ###        
        s_form = self.form.subscriber;
        ip_panel = wx.Panel(self)
        ip_sizer_v = wx.BoxSizer(wx.VERTICAL)
        ip_sizer = wx.BoxSizer(wx.HORIZONTAL)

        ip_id = Entry.Static ( s_form.table["subscriberid"], ip_panel,
                              variable = s_form.getvar("subscriberid")                           
                              )
        ip_id.SetForegroundColour (wx.Color(40,20,20))
        ip_id.SetFont ( wx.Font (17, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD) )                

        ip_name = Entry.Static ( s_form.table["name"], ip_panel,
                              variable = s_form.getvar("name")
                              )
        ip_name.SetForegroundColour (wx.Color(40,70,20))
        ip_name.SetFont ( wx.Font (17, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD) )        
        
        ip_loc = Entry.StaticReference ( s_form.table["primarylocationid"], ip_panel,
                              variable = s_form.getvar("primarylocationid")                           
                              )
        ip_loc.SetForegroundColour (wx.Color(20,20,20))
        ip_loc.SetFont ( wx.Font (17, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL) )
        
        ip_sizer.Add (ip_id,1,  flag=wx.EXPAND)
        ip_sizer.Add (ip_name, 5, flag=wx.EXPAND)
        ip_sizer.Add ( ip_loc, 5, flag=wx.EXPAND)
        
        ip_sizer_v.Add ( ip_sizer, flag=wx.EXPAND)
        
        
        ip_panel.SetSizer(ip_sizer_v)
        #sizer_v3.Add ( ip_panel, 1, flag=wx.EXPAND )
        #############################################################################
        def _format_service(r):
            return r.typeofservice_REF + "\n" + r.classofservice_REF
        self.recordlist.services = rl.RecordList(self.store.services, self,
                                                 reprfunc = _format_service)
        self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber)


        self.mgr.AddPane ( ip_panel, wx.aui.AuiPaneInfo().Top().
                           Floatable(False).CloseButton(False).
                           Name("subscriber_info").
                           Caption("Klient").                           
                           MinSize( (-1, 200) )
                           )
        self.mgr.AddPane ( self.editor.subscriber, wx.aui.AuiPaneInfo().Center().
                           Floatable(False).CloseButton(False).
                           Name("subscriber_editor").
                           Caption("Podstawowe dane klienta").
                           Position(0).
                           MinSize( (-1, 250) )
                           )        
        self.mgr.AddPane ( self.recordlist.services, wx.aui.AuiPaneInfo().Center().
                           Floatable(False).CloseButton(False).
                           Name("service_list").
                           Position(1).
                           Caption("Usługi")
                            )
                           

        self.mgr.Update()

        
        
        #sizer_h4 = wx.BoxSizer (wx.HORIZONTAL)

        #sizer_v3.Add ( sizer_h4, 5, wx.EXPAND )

        #sizer_v5 = wx.BoxSizer (wx.VERTICAL)
        #sizer_v6 = wx.BoxSizer (wx.VERTICAL)
        
        #sizer_h4.Add ( sizer_v5, 2, wx.EXPAND )
        #sizer_h4.Add ( sizer_v6, 2, wx.EXPAND )
        
        
        #subscroll = ScrolledGenericForm(self.form.subscriber, self)
        #self.editor.subscriber = subscroll.genericform                
        
        #sizer_v5.Add ( subscroll, 4, wx.EXPAND  )

        #def _format_service(r):
            #return r.typeofservice_REF + "\n" + r.classofservice_REF
        #self.recordlist.services = rl.RecordList(self.store.services, self,
                                                 #reprfunc = _format_service)

        #self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber)
        
        #sizer_v5.Add ( self.recordlist.services, 3, wx.EXPAND )
        
        #sizer_v6.Add ( wx.StaticText ( self, label="URZ. IP. MAC / Notes"), 1, wx.EXPAND )
        
        self.form.subscriber.setid ( self.store.subscriber[0].objectid )
        
        #self.SetSizer(sizer_v1)
        #self.SetAutoLayout(1)

        
        
        
        
        
        