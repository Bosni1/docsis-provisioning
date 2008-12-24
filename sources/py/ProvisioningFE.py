#!/bin/env python
##$Id$
from ProvCon.dbui.database import CFG
import ProvCon.dbui.database as db
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk

import wx


import time, traceback

db.RaiseDBException = guitk.DBErrorHandler

class ProvisioningFE(wx.App):
    def OnInit(self):
        
        self.toplevel = wx.Frame (None, title="Provisioning", size=(1100,800))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.toplevel.SetSizer (sizer)
        self.toplevel.Show()

        self.subseditor = guitk.complete.CompleteGenericForm ( self.toplevel, tablename="class_of_service"
                                                                )
        sizer.Add (self.subseditor, 4, flag=wx.EXPAND)
        
        return True
    
        
app = ProvisioningFE()
app.MainLoop()






