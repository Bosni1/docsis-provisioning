#!/bin/env python
from ProvCon.func.decorators import singleentry
from ProvCon.dbui import orm, forms
from ProvCon.dbui import wxwin as guitk

import wx

class topwindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="ProvisioningFE", size=(1024,800))
        self.form = forms.Form ( orm.Table.Get ( "table_info" ) )
        self.editor = guitk.forms.GenericForm ( self.form, self )
        self.editor.create_widget()
        self.editor.Show()
        self.form.setid (16)
        
        
        
app = wx.App()
top = topwindow()
top.Show()
app.MainLoop()







