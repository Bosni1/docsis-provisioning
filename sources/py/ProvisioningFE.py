#!/bin/env python
from ProvCon.dbui.database import CFG
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk

import wx
from wx.lib import scrolledpanel as scrolled

class topwindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="ProvisioningFE", size=(600,400))
        self.editor = guitk.complete.CompleteGenericForm ( "table_info", self )
        
        #self.form = orm.Form ( meta.Table.Get ( "table_info" ) )
        #self.editor = guitk.forms.GenericForm ( self.form, self )
        #self.editor.create_widget()
        #self.editor.Show()
        #self.editor.form.setid (18)
        return
        win = wx.ScrolledWindow( self, -1 )
        
        child = wx.Panel ( win )
        flex = wx.FlexGridSizer(cols=2)

        for i in range(200):
            s = wx.StaticText ( child, -1, "LABEL %d [%s]" % (i, "*" * i) )
            flex.Add (s, border=1 )
        
        child.SetSizer(flex)
        
        win.SetAutoLayout(1)
        
        win.SetScrollbars(20,20,50,50)
        
        
        
        
app = wx.App()
top = topwindow()
top.Show()
app.MainLoop()







