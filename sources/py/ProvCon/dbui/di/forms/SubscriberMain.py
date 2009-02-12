# -*- coding: utf8 -*-
from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin.forms import GenericForm, ScrolledGenericForm, GenerateEditorDialog
from ProvCon.dbui.wxwin import recordlists as rl, mwx, forms
from ProvCon.dbui.wxwin.fields import Entry
from app import APP
import wx
import wx.aui
import wx.lib.scrolledpanel as scroll
import wx.lib.rcsizer as rcs

NewSubscriberDialog = GenerateEditorDialog ( "subscriber", 
                        "Nowy klient...", 
                        excluded=["primarylocationid", "postaladdress", "email", "telephone"] )

class SubscriberSearchToolbar(wx.Panel):

    def __init__(self, main, *args, **kw):
        wx.Panel.__init__ (self, main)

        self.main = main
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.searchctrl = wx.SearchCtrl (self, style=wx.TE_PROCESS_ENTER)
        self.recordlist = orm.GenericQueryRecordList ( "SELECT NULL LIMIT 0" )
        self.resultspopup = mwx.RecordListCombo (self, self.recordlist)
        sizer.Add ( wx.StaticText ( self, label="Szukaj: " ), flag=wx.ALIGN_CENTER )        
        sizer.Add ( self.searchctrl, 10, flag=wx.ALIGN_CENTER)
        self.results_txt = wx.StaticText ( self, label="  Wyniki (   ): " )
        sizer.Add ( self.results_txt, flag=wx.ALIGN_CENTER )        
        sizer.Add ( self.resultspopup, 14, flag=wx.ALIGN_CENTER)
        sizer.Add ( wx.Button(self, label="<<"), flag=wx.ALIGN_CENTER )
        sizer.Add ( wx.Button(self, label=">>"), flag=wx.ALIGN_CENTER )

        self.recordlist.reload()

        self.resultspopup.listenForEvent("current_record_changed", main.setCurrentRecord)
        
        self.SetSizer(sizer)
        
        self.searchctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_search)
        self.searchctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.on_cancel)
        self.searchctrl.Bind(wx.EVT_TEXT_ENTER, self.on_do_search)
        
    def on_search(self, evt):
        pass
    
    def on_cancel(self, evt):
        pass
    
    def on_do_search(self, evt):    
        self.recordlist.query = "SELECT s.* FROM pv.subscriber s INNER JOIN pv.object_search_txt t ON s.objectid = t.objectid WHERE t.txt ~* '%s'" % self.searchctrl.GetValue() 
        self.recordlist.reload(feed=True)
        self.results_txt.Label  = "Wyniki (%d) :" % len(self.recordlist)
        if len(self.recordlist) > 0:
            oid = self.recordlist[0].objectid
            wx.CallLater (100, self.resultspopup.set_oid, oid)
            wx.CallLater (100, self.main.setCurrentRecord, self.recordlist[0] )
    
        
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

        self.sizer.Add (self.row_1,10,flag=wx.EXPAND)

        ##Save option
        self.row_2 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.row_2.AddStretchSpacer(5)

        txt = wx.StaticText ( self, label="DANE ZOSTAŁY ZMIENIONE")
        txt.Font = font18        
        self.row_2.Add ( txt, flag=wx.ALIGN_CENTER_VERTICAL )
        
        self.row_2.AddSpacer ( 40 )

        btn = wx.Button ( self, label="Zapisz!")
        btn.Font = font22b
        btn.ForegroundColour = "RED"
        self.row_2.Add ( btn, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.row_2.AddSpacer ( 40 )        
        
        self.sizer.Add ( self.row_2,0,wx.EXPAND)
                        
        self.SetSizer (self.sizer)
        
        self.sizer.Hide(self.row_2)

    def showSaveOption(self):
        self.sizer.Show (self.row_2)

    def hideSaveOption(self):
        self.sizer.Hide (self.row_2)
        


class SubscriberCommandPanel(wx.Panel):
    def __init__(self, main, form, *args, **kwargs):
        wx.Panel.__init__(self, main, *args, **kwargs)
        sizer = wx.BoxSizer (wx.VERTICAL)
        
        self.main = main
        self.form = form
        self.buttons = AttrDict()
        self.buttons.new_subscriber = wx.Button ( self, label = "Nowy\nklient", style=wx.NO_BORDER )
        self.buttons.new_device = wx.Button ( self, label = "Nowe\nurządzenie", style=wx.NO_BORDER )
        self.buttons.new_contact = wx.Button ( self, label = "Nowe\nzgłoszenie", style=wx.NO_BORDER )
        self.buttons.cos_change = wx.Button ( self, label = "Zmiana\npakietu", style=wx.NO_BORDER )
        self.buttons.status_change = wx.Button ( self, label = "Diagnostyka", style=wx.NO_BORDER )
        self.buttons.diagnostics = wx.Button ( self, label = "Blokady", style=wx.NO_BORDER )
        self.buttons.service_change = wx.Button ( self, label = "Przełączenie", style=wx.NO_BORDER )
        self.buttons.equipment_change = wx.Button ( self, label = "Wymiana\nsprzętu", style=wx.NO_BORDER )        
        for b in self.buttons:
            bt = self.buttons[b]            
            sizer.Add ( bt,0, flag=wx.EXPAND)
            if hasattr(self, "on_" + b): 
                bt.Bind ( wx.EVT_BUTTON, getattr(self, "on_" + b ) )
        
        sizer.AddStretchSpacer (10)
        
        self.SetSizer(sizer)

        self.new_subscriber_dialog = None
        
    def on_new_subscriber(self, evt, *args):
        if not self.new_subscriber_dialog:
            self.new_subscriber_dialog = NewSubscriberDialog(self.main)
        
        self.new_subscriber_dialog.New ()
        self.new_subscriber_dialog.Edit()
        objectid = self.new_subscriber_dialog.form.current._objectid
        if objectid:
            APP.DataStore["subscriber"].reloadsingle ( objectid )
            self.main.setCurrentSubscriberId ( objectid )
            
class SubscriberMain(wx.Panel):
    
    def __init__(self, parent, *args):
        wx.Panel.__init__(self, parent, *args)
        
        self.form = AttrDict()
        self.table = AttrDict()
        self.editor = AttrDict()
        self.store = AttrDict()
        self.recordlist = AttrDict()
        self.dialogs = {
            "service" : forms.GenerateEditorDialog ( "service", "Usługa"),            
            }
        
        self.table.subscriber = meta.Table.Get ( "subscriber" )
        self.table.service = meta.Table.Get ( "service" )
        
        self.store.subscriber = orm.RecordList ( self.table.subscriber ).reload()
        self.store.services = orm.RecordList ( self.table.service, select=["classofservice","typeofservice","handle"] )
        self.form.subscriber = orm.Form ( self.table.subscriber  )
        subscriberRec = self.form.subscriber.current
        subscriberRec.enableChildren ()        
        
        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow (self)
        
        subscroll = ScrolledGenericForm(self.form.subscriber, self)
        self.editor.subscriber = subscroll.genericform                        
        
        self.info_panel = SubscriberInfoPanel(self, self.form.subscriber)
        self.command_panel = SubscriberCommandPanel(self, self.form.subscriber)
        
        def _format_service(r):
            return r.typeofservice_REF + "\n<br>" + r.classofservice_REF
                
        #self.recordlist.services = rl.RecordList(self.store.services, self,
        #                                         reprfunc = _format_service)
        
        self.recordlist.services = rl.RecordList(subscriberRec.list_service_subscriberid, self,
                                                 reprfunc = _format_service)        
        #self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber)

        
        self.mgr.AddPane ( self.info_panel, wx.aui.AuiPaneInfo().Top().
                           Floatable(False).CloseButton(False).
                           Caption("Podsumowanie danych klienta").
                           Name("info_panel").
                           Layer(1).
                           MinSize( (-1, 170) ).
                           BestSize( (700,170) )
                           )
        self.mgr.AddPane ( SubscriberSearchToolbar(self), wx.aui.AuiPaneInfo().Bottom().
                           CloseButton(True).Floatable(False).Dockable(False).Show().
                           Name("search_results").
                           Caption("Wyniki wyszukiwania...").
                           Layer(1).
                           MinSize( ( -1, 40) )
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

        self.mgr.Update()

        
        f = self.form.subscriber
        f.listenForEvent ( "request_record_change", self.subscriberRecordChanged )
        f.listenForEvent ( "current_record_modified", self.subscriberRecordModified )
        f.listenForEvent ( "current_record_deleted", self.subscriberRecordDeleted )
        f.listenForEvent ( "current_record_saved", self.subscriberRecordSaved )
        f.listenForEvent ( "data_loaded", self.subscriberDataLoaded )
        
        self.form.subscriber.setid ( self.store.subscriber[10].objectid )
        #self.form.subscriber.new()
              
        
    def setCurrentRecord(self, record):
        self.setCurrentSubscriberId ( record.objectid )
        
    def setCurrentSubscriberId(self, objectid):
        wx.CallLater ( 100, self.form.subscriber.setid, objectid )
        #self.form.subscriber.setid ( record.objectid )
        
    def subscriberRecordChanged(self, *args):
        print args
        
    def subscriberRecordModified(self, *args):
        self.info_panel.showSaveOption()
        
    def subscriberRecordDeleted(self, *args):
        print args
        
    def subscriberRecordSaved(self, *args):
        self.info_panel.showSaveOption()
        
    def subscriberDataLoaded(self, *args):
        self.info_panel.hideSaveOption()
        
        
        