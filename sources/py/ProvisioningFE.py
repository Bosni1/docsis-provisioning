#!/bin/env python
##$Id$
from ProvCon.dbui.database import CFG
import ProvCon.dbui.database as db
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk
from ProvCon.func import AttrDict
import wx


import time, traceback

db.RaiseDBException = guitk.DBErrorHandler

class ProvisioningFE(wx.App):
    def OnInit(self):
        self.windows = AttrDict()
        self.windows.toplevel = wx.Frame (None, title="Provisioning", size=(1100,800))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.windows.toplevel.SetSizer (sizer)
        self.windows.toplevel.Show()
        
        self.subseditor = guitk.complete.CompleteGenericForm ( self.windows.toplevel, 
                                                               tablename="class_of_service"
                                                                )
        sizer.Add (self.subseditor, 4, flag=wx.EXPAND)
        
        return True
    
        
app = ProvisioningFE()
app.MainLoop()






