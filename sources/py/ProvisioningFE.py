#!/bin/env python
##$Id$
from ProvCon.dbui.database import CFG, Init
import ProvCon.dbui.database as db
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk
from ProvCon.dbui.di.forms.SubscriberMain import SubscriberMain
from ProvCon.func import AttrDict
import ProvCon.dbui.di.controls as controls
import wx
import wx.html as html


import time, traceback

db.RaiseDBException = guitk.DBErrorHandler

class ProvisioningFE(wx.App):
    def OnInit(self):
        self.windows = AttrDict()
        self.forms = AttrDict()
        self.windows.toplevel = wx.Frame (None, title="Provisioning", size=(1100,900))
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        notebook = wx.Notebook (self.windows.toplevel)        
        self.windows.notebook = notebook

        
        welcome = html.HtmlWindow ( notebook )        
        self.windows.welcome = welcome        
        welcome.SetPage ( """
        <br/><center>
        <H1>NETCON 3.0 Panel administracyjny</H1>
        <h2>$Revision$</h2>
        </center>
        <br/><br/>
        """ )
        notebook.AddPage ( welcome, "Powitanie" )
        
        ##LOCATIONS
        locations = controls.LocationEditor ( notebook )
        self.windows.locations = locations
        notebook.AddPage ( locations, "Lokalizacje" )
        
        #self.forms.subseditor = guitk.complete.CompleteGenericForm ( notebook, 
        #                                                       tablename="subscriber"
        #                                                      )
        subscriber = SubscriberMain(notebook)
        notebook.AddPage ( subscriber, "Klient" )
        
        datastore = wx.Panel(notebook)
        notebook.AddPage (datastore, "DATA STORE")
        
        sizer.Add (self.windows.notebook, 4, flag=wx.EXPAND)                        
        self.windows.toplevel.SetSizer (sizer)
        self.windows.toplevel.Show()
        

        return True


Init()        
app = ProvisioningFE()
import cProfile
cProfile.run( "app.MainLoop()", "/tmp/prov-prof" )
import pstats
p = pstats.Stats ("/tmp/prov-prof" )
p.strip_dirs().sort_stats(-1).print_stats()
#app.MainLoop()






