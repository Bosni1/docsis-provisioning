# -*- coding: utf8 -*-
from ProvCon.func import AttrDict, partial
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
                        excluded=["primarylocationid", "postaladdress", "email", "telephone"],
                        height=200)

ServiceDialog = GenerateEditorDialog ( "service",
                                       "Usługa",
                                       fixed={'subscriberid' : None })
                                       

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
        self.results_txt = wx.StaticText ( self, label="  Wyniki (    ): " )
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
        self.recordlist.query = "SELECT s.*, t.txt as _astxt FROM pv.subscriber s INNER JOIN pv.object_search_txt t ON s.objectid = t.objectid WHERE t.txt ~* '%s'" % self.searchctrl.GetValue() 
        self.recordlist.reload (feed=True)
        self.results_txt.Label  = "Wyniki (%4d) :" % len(self.recordlist)
        if len(self.recordlist) > 0:
            oid = self.recordlist[0].objectid
            wx.CallAfter (self.resultspopup.set_oid, oid)
            wx.CallAfter (self.main.setCurrentRecord, self.recordlist[0] )
    
        
class SubscriberInfoPanel(wx.Panel):
    
    def __init__(self, parent, form, *args, **kwargs):
        from ProvCon.dbui.wxwin.art import BITMAPS
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
        self.row_1.Add ( self.edit.subscriberid, row=1, col=1, rowspan=2, border=30, flag=wx.EXPAND )
        self.row_1.Add ( self.edit.name, row=1,col=2, flag=wx.EXPAND)
        self.row_1.Add ( self.edit.primarylocation, row=2,col=2, flag=wx.EXPAND)

        self.sizer.Add (self.row_1,10,flag=wx.EXPAND)

        ##Save option
        self.row_2 = wx.BoxSizer(wx.HORIZONTAL)
        #self.row_2.Add ( wx.StaticBitmap (self, bitmap=BITMAPS.WRITE) )
        
        self.row_2.AddStretchSpacer(5)

        txt = wx.StaticText ( self, label="DANE ZOSTAŁY ZMIENIONE")
        #txt.Font = font18        
        self.row_2.Add ( txt, flag=wx.ALIGN_CENTER_VERTICAL )
        
        self.row_2.AddSpacer ( 40 )

        btn = wx.BitmapButton ( self, bitmap=BITMAPS.WRITE)
        btn.Bind (wx.EVT_BUTTON, self.doSave)
        self.row_2.Add ( btn, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.row_2.AddSpacer ( 40 )        
        
        self.sizer.Add ( self.row_2,0,wx.EXPAND)
                        
        self.SetSizer (self.sizer)        
        self.sizer.Hide(self.row_2)

    def showSaveOption(self):
        self.sizer.Show (self.row_2)
        self.Layout()

    def hideSaveOption(self):
        self.sizer.Hide (self.row_2)
        
    def doSave(self, evt, *args):
        self.form.save()

class SubscriberCommandPanel(wx.Panel):
    def __init__(self, main, form, *args, **kwargs):
        from ProvCon.dbui.wxwin.art import BITMAPS
        wx.Panel.__init__(self, main, *args, **kwargs)
        sizer = wx.BoxSizer (wx.VERTICAL)
        
        self.main = main
        self.form = form
        self.buttons = AttrDict()
        self.buttons.new_subscriber = wx.BitmapButton ( self, bitmap = BITMAPS.ADDUSER, style=wx.NO_BORDER )
        self.buttons.new_subscriber.SetToolTipString ( "Dodaj nowego klienta" )
        
        self.buttons.new_service = wx.BitmapButton ( self, bitmap = BITMAPS.ADDSERVICE, style=wx.NO_BORDER )
        self.buttons.new_service.SetToolTipString ( "Dodaj nową usługę" )

        self.buttons.new_issue = wx.BitmapButton ( self, bitmap = BITMAPS.SUPPORT, style=wx.NO_BORDER )
        self.buttons.new_issue.SetToolTipString ( "Nowe zgłoszenie" )
        
        #self.buttons.new_device = wx.Button ( self, label = "Nowe\nurządzenie", style=wx.NO_BORDER )        
        #self.buttons.cos_change = wx.Button ( self, label = "Zmiana\npakietu", style=wx.NO_BORDER )
        #self.buttons.status_change = wx.Button ( self, label = "Diagnostyka", style=wx.NO_BORDER )
        #self.buttons.diagnostics = wx.Button ( self, label = "Blokady", style=wx.NO_BORDER )
        #self.buttons.service_change = wx.Button ( self, label = "Przełączenie", style=wx.NO_BORDER )
        #self.buttons.equipment_change = wx.Button ( self, label = "Wymiana\nsprzętu", style=wx.NO_BORDER )
        
        for b, bt in self.buttons.inorder():            
            sizer.Add ( bt,0, flag=wx.EXPAND)
            if hasattr(self, "on_" + b): 
                bt.Bind (wx.EVT_BUTTON, partial(self._run_handler, "on_" + b ) )
        
        sizer.AddStretchSpacer (10)
        
        self.SetSizer(sizer)

        self.new_subscriber_dialog = None        
    def _run_handler (self, hname, evt, *args):
        if hasattr(self, hname):
            wx.CallAfter ( getattr(self, hname), evt, *args )
            
    def on_new_subscriber(self, evt, *args):
        self.main.addNewSubscriber()
        
    def on_new_service(self, evt, *args):
        self.main.addNewService()

class IPListMenu (rl.RecordListMenu):
    def __init__(self, main, recordlist, **kw):
        rl.RecordListMenu.__init__(self, recordlist, **kw)
        self.main = main
        self.AddItem ( "new", "Dodaj nowy adres IP" )
        self.AddItem ( "del", "Usuń {0.address}")
        self.AddItem ( "block", "Zablokuj {0.address}" )
        self.AddItem ( "unblock", "Odblokuj {0.address}" )
        self.AddItem ( "spamon", "Włącz blokadę poczty dla {0.address}" )
        self.AddItem ( "spamoff", "Usuń blokadę poczty dla {0.address}" )
        self.AddItem ( "child", "Ustaw child-protection" )
        self.AddItem ( "settings", "Pokaż ustawienia sieci" )
        self.AppendSeparator()
        self.AddItem ( "ping", "Ping {0.address}" )
        self.AddItem ( "traceroute", "Traceroute {0.address}" )
        self.AppendSeparator()
        self.AddItem ( "copy", "Kopiuj do schowka" )        

    def prepare(self):
        rec = rl.RecordListMenu.prepare(self)    
        for n in self.unformatted:
            item, fmt = self.unformatted[n]
            if not rec and n <> "new":
                item.Enable(False)
            else:
                item.Enable(True)
        
        
class ServiceListMenu (rl.RecordListMenu):
    def __init__(self, main, recordlist, **kw):
        rl.RecordListMenu.__init__(self, recordlist, **kw)                
        self.main = main
        self.AddItem ( "ticket", "Zgłoszenie/Awaria usługi" )
        self.AddItem ( "history", "Historia usługi" )
        self.AppendSeparator()
        self.AddItem ( "change_cos", "Zmiana pakietu" )
        self.AddItem ( "block", "Blokada usługi" )
        self.AddItem ( "suspend", "Zawieszenie usługi" )
        self.AddItem ( "disconnect", "Wyłączenie usługi" )
        self.AppendSeparator()
        self.AddItem ( "service_check", "Sprawdzenie działania usługi" )
        self.AppendSeparator()
        self.AddItem ( "add", "Dodaj nową usługę" )        
        self.AddItem ( "del", "Usuń usługę" )                            

    def on_add(self, record, *args):
        wx.CallAfter(self.main.addNewService)
        
    def prepare(self):
        rec = rl.RecordListMenu.prepare(self)    
        for n in self.unformatted:
            item, fmt = self.unformatted[n]
            if not rec and n <> "add":
                item.Enable(False)
            else:
                item.Enable(True)
                
class MACListMenu (rl.RecordListMenu):
    def __init__(self, main, recordlist, **kw):
        rl.RecordListMenu.__init__(self, recordlist, **kw)                
        self.main = main
        self.AddItem ( "add", "Dodaj nowy MAC" )
        self.AddItem ( "del", "Usuń adres MAC" )
        self.AppendSeparator()
        self.AddItem ( "change_dhcp", "Zmień mapowanie DHCP" )
        self.AddItem ( "extra_dhcp", "Ustaw dodatkowe opcje DHCP" )
        self.AddItem ( "change_nas", "Zmień urządzenie dostępowe" )        
        self.AddItem ( "find", "Znajdź w FDB" )
        self.AddItem ( "make_static", "Ustaw static-arp" )
        self.AppendSeparator()
        self.AddItem ( "history", "Historia wykorzystania adresu MAC" )
        self.AppendSeparator()
        self.AddItem ( "copymac", "Kopiuj MAC do schowka" )        
        self.AddItem ( "copyip", "Kopiuj IP do schowka" )        

class DeviceListMenu (rl.RecordListMenu):

    def __init__(self, main, recordlist, **kw):
        rl.RecordListMenu.__init__(self, recordlist, **kw)                
        self.main = main
        self.AddItem ( "add", "Dodaj nowe urządzenie" )
        self.AddItem ( "del", "Usuń urządzenie z listy" )
        self.AppendSeparator()
        self.AddItem ( "edit", "Przejdź do edytora urządzeń" )
        self.AddItem ( "service_check", "Sprawdzenie działania urządzenia" )
        self.AddItem ( "ping", "Ping" )
        self.AddItem ( "traceroute", "Traceroute" )
        
        self.cable_modem_submenu = rl.RecordListMenu ( recordlist, handler=self )
        sub = self.cable_modem_submenu
        sub.AddItem ( "cm_info", "Informacje o pracy modemu" )
        sub.AddItem ( "cm_monitor", "Pokaż na monitorze modemów" )
        sub.AddItem ( "cm_monitor_building", "Pokaż cały budynek na monitorze modemów" )
        sub.AddItem ( "cm_restart", "Restart modemu" )
        sub.AddItem ( "cm_ubr_purge", "Wyczyść wpis na CMTSie" )
        self.AppendSubMenu ( sub, "Modem kablowy" )

        self.mikrotik_submenu = rl.RecordListMenu ( recordlist, handler=self )
        sub = self.mikrotik_submenu
        sub.AddItem ( "mikro_info", "Informacje o pracy urządzenia" )
        sub.AddItem ( "mikro_restart", "Restart" )
        sub.AddItem ( "mikro_qos", "Ustaw kolejki QoS" )
        sub.AddItem ( "mikro_port_redir", "Ustaw przekierowanie portów" )
        sub.AddItem ( "mikro_winbox", "Winbox" )        
        sub.AddItem ( "mikro_ssh", "SSH" )
        sub.AddItem ( "mikro_nas_ssh", "SSH na NAS" )
        self.AppendSubMenu ( sub, "Mikrotik" )
        
        
        self.AppendSeparator()
        self.AddItem ( "history", "Historia wykorzystania urządzenia" )

        
class SubscriberMain(wx.Panel):
    
    def __init__(self, parent, *args):
        from ProvCon.dbui.di import rSubscriber
        wx.Panel.__init__(self, parent, *args)
        
        self.form = AttrDict()
        self.table = AttrDict()
        self.editor = AttrDict()
        self.store = AttrDict()
        self.recordlist = AttrDict()
        self.dialogs = AttrDict()
        self.dialogs.service = ServiceDialog(self)
        self.dialogs.subscriber = NewSubscriberDialog(self)
        
        self.table.subscriber = meta.Table.Get ( "subscriber" )
        self.table.service = meta.Table.Get ( "service" )
        
        self.store.subscriber = APP.DataStore.subscriber
        self.store.services = orm.RecordList ( self.table.service, select=["classofservice","typeofservice","handle"] )
        
        self.form.subscriber = orm.Form ( self.table.subscriber, recordclass = rSubscriber  )
        subscriberRec = self.form.subscriber.current
        subscriberRec.enableChildren()                
        
        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow (self)
        
        subscroll = ScrolledGenericForm(self.form.subscriber, self)
        self.editor.subscriber = subscroll.genericform                        
        
        self.info_panel = SubscriberInfoPanel(self, self.form.subscriber)
        self.command_panel = SubscriberCommandPanel(self, self.form.subscriber)
        
        def _format_service(r):
            return "<b>" + r.typeofservice_REF + "</b> " + r.classofservice_REF + "<br><i>" + r.locationid_REF + "</i>"
        def _format_ip(r):
            return "<b>" + r.address + "</b>"
        def _format_mac(r):                        
            fmt = "<tt><b>" + r.mac + "</b></tt>&nbsp;&nbsp; "
            if r.ipreservationid:
                fmt += " -&gt; <b>" + r.ipreservationid_REF + "</b>"
            return fmt
        def _format_device(r):                        
            return r._astxt
        
        #self.recordlist.services = rl.RecordList(self.store.services, self,
        #                                         reprfunc = _format_service)
        
        self.recordlist.services = rl.RecordList(subscriberRec.list_service_subscriberid, self,
                                                 reprfunc = _format_service)
        self.recordlist.services.set_menu ( ServiceListMenu(self, self.recordlist.services) )

        self.recordlist.ip = rl.RecordList(subscriberRec.ipreservations, self, reprfunc = _format_ip )
        self.recordlist.ip.set_menu ( IPListMenu(self, self.recordlist.ip) )

        self.recordlist.mac = rl.RecordList(subscriberRec.macaddresses, self, reprfunc = _format_mac )        
        self.recordlist.mac.set_menu ( MACListMenu(self, self.recordlist.mac) )
        
        self.recordlist.devices = rl.RecordList(subscriberRec.devices, self, reprfunc = _format_device )        
        self.recordlist.devices.set_menu (DeviceListMenu(self, self.recordlist.devices))
        #self.recordlist.services.bind_to_form ( "subscriberid", self.form.subscriber)

        
        self.mgr.AddPane ( self.info_panel, wx.aui.AuiPaneInfo().Top().
                           Floatable(False).CloseButton(False).
                           Caption("Podsumowanie danych klienta").
                           Name("info_panel").
                           Layer(1).
                           MinSize( (-1, 100) ).
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
        self.mgr.AddPane ( self.recordlist.devices, wx.aui.AuiPaneInfo().Bottom().
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

        self.mgr.AddPane ( self.recordlist.mac, wx.aui.AuiPaneInfo().Right().
                           CloseButton(False).Floatable(False).
                           Name("mac_address_list").Caption("MAC").
                           Layer(1).
                           MinSize( (300,-1) )                           
                           )
        
        self.mgr.AddPane ( self.recordlist.ip, wx.aui.AuiPaneInfo().Right().
                           CloseButton(False).Floatable(False).
                           Name("ip_address_list").Caption("Adresy IP").
                           Layer(1).                           
                           MinSize( (300,-1) )                           
                           )

        self.mgr.Update()

        
        f = self.form.subscriber
        f.listenForEvent ( "request_record_change", self.subscriberRecordChange )
        f.listenForEvent ( "current_record_modified", self.subscriberRecordModified )
        f.listenForEvent ( "current_record_deleted", self.subscriberRecordDeleted )
        f.listenForEvent ( "current_record_saved", self.subscriberRecordSaved )
        f.listenForEvent ( "data_loaded", self.subscriberDataLoaded )
        
        #self.form.subscriber.setid ( self.store.subscriber[0].objectid )
        #self.form.subscriber.new()
              
    def getCurrentSubscriberRecord(self):
        return self.form.subscriber.current
    
    def setCurrentRecord(self, record):
        self.setCurrentSubscriberId ( record.objectid )
        
    def setCurrentSubscriberId(self, objectid):
        wx.CallLater ( 100, self.form.subscriber.setid, objectid )
        #self.form.subscriber.setid ( record.objectid )
        
    def subscriberRecordChange(self, *args):
        print args
        
    def subscriberRecordModified(self, *args):
        self.info_panel.showSaveOption()
        
    def subscriberRecordDeleted(self, *args):
        print args
        
    def subscriberRecordSaved(self, *args):
        self.info_panel.hideSaveOption()
        
    def subscriberDataLoaded(self, *args):
        self.getCurrentSubscriberRecord().reloadIpReservations()
        self.getCurrentSubscriberRecord().reloadMACAddresses()
        self.info_panel.hideSaveOption()
    
    def addNewSubscriber(self, *args):
        dlg = self.dialogs.subscriber
        dlg.New ()
        dlg.Edit()
        objectid = dlg.form.current.objectid

        if objectid:
            APP.DataStore["subscriber"].reloadsingle ( objectid )
            self.main.setCurrentSubscriberId ( objectid )

    
    def addNewService(self, *args):
        dlg = self.dialogs.service
        rec = self.getCurrentSubscriberRecord()
        if not rec.hasData: return
        dlg.form.set_fixed_value ( 'subscriberid', rec.objectid )
        dlg.New()        
        dlg.form["locationid"] = rec.primarylocationid
        dlg.Edit()
        objectid = dlg.form.current.objectid

        if objectid:
            APP.DataStore["service"].reloadsingle ( objectid )
            self.getCurrentSubscriberRecord().list_service_subscriberid.reload()            


    