#!/bin/env python
##$Id$
from ProvCon.dbui.database import CFG, Init
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk
from ProvCon.dbui.di import controls as datacontrols

import wx
import wx.aui as aui

#from wx.lib import scrolledpanel as scrolled

__revision__ = "$Revision$"

class MetaDataEditor(wx.App):
    def OnInit(self):
        
        self.toplevel = wx.Frame (None, title="Provisioning meta-data editor", size=(1100,800))

        sizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        lsizer = wx.BoxSizer(wx.VERTICAL)
        
        ##table info editor
        self.tableeditor = guitk.complete.CompleteGenericForm ( self.toplevel, tablename="table_info",
                                                                navigator = False,
                                                                no_NEW = True, no_DEL = True)
        lsizer.Add (self.tableeditor, 4, flag=wx.EXPAND)
        
        
        fieldinfotable = meta.Table.Get ( "field_info" )
        
        self.fieldrecords = orm.RecordList ( fieldinfotable, select=['lp', 'name','path','label'], order="lp" )
        self.fieldrecords.filterfunc = lambda r: r.name not in meta.Table.__special_columns__        
        
        def _fieldrepr(r):
            return '#{0.lp}. <b>{0.path}</b><br>&nbsp;&nbsp;<i>{0.label}</i><hr>'.format(r)
        self.fieldlist = guitk.recordlists.RecordList (self.fieldrecords, self.toplevel,
                                                       reprfunc = _fieldrepr)                
        
        self.fieldlist.bind_to_form ( "classid", self.tableeditor.form )
        
        lsizer.Add (self.fieldlist, 2, flag=wx.EXPAND)
                               
        rsizer = wx.BoxSizer (wx.VERTICAL)
        self.fieldeditor = guitk.complete.CompleteGenericForm ( self.toplevel, table = fieldinfotable,
                                                                navigator = False,
                                                                no_NEW = True, no_DEL = True)
        self.fieldeditor.set_navigator ( self.fieldlist )
        rsizer.Add ( self.fieldeditor, 1, flag=wx.EXPAND )
        
        hsizer.Add(lsizer, 1, flag=wx.EXPAND)
        hsizer.Add(rsizer, 1, flag=wx.EXPAND)
        sizer.Add (hsizer, 1, flag=wx.EXPAND)

        tablenav = guitk.navigators.Navigator (self.toplevel)
        tablenav.set_records ( orm.RecordList ( self.tableeditor.table ).reload() )        
        sizer.Add (tablenav, 0, flag=wx.EXPAND)
        tablenav.navigate (0)
        tablenav.Show()
        
        self.tableeditor.set_navigator ( tablenav )
        
        self.toplevel.SetSizer (sizer)

        menu = wx.MenuBar()
        menu_data = wx.Menu()
        
        mi_export = menu_data.Append (wx.NewId(), "&Export", "Export meta-data to a text file." )
        mi_import = menu_data.Append (wx.NewId(), "&Import", "Import meta-data to a text file." )

        self.Bind (wx.EVT_MENU, self.ExportData, id=mi_export.GetId() )
        self.Bind (wx.EVT_MENU, self.ImportData, id=mi_import.GetId() )
        
        menu.Append ( menu_data, "&Data" )
        self.toplevel.SetMenuBar ( menu )
        
        self.toplevel.Show()
        
        return True
    
    def ExportData(self, *args):
        dlg = wx.FileDialog(self.toplevel, message="Export to file...",
                    style=wx.SAVE,
                    wildcard = "Meta-Data backup (*.md) |*.md|"  \
                               "All files (*.*)|*.*" )
        if dlg.ShowModal() == wx.ID_OK:
            from ProvCon.dbui.di import meta
            meta.ExportMetaData ( dlg.GetPath() )
        dlg.Destroy()
        
    def ImportData(self, *args):
        dlg = wx.FileDialog(self.toplevel, message="Import from file...",
                            style=wx.OPEN,
                            wildcard = "Meta-Data backup (*.md) |*.md|"  \
                                       "All files (*.*)|*.*" )
        if dlg.ShowModal() == wx.ID_OK:
            from ProvCon.dbui.di import meta
            filename = dlg.GetPath()
            dlg.Destroy()            
            dlg = wx.ProgressDialog ("Import danych z " + dlg.GetPath(), "Importowanie...",
                                     parent = self.toplevel)
            dlg.Size = wx.Size(400, 120)
            dlg.Show()
            for msg in meta.ImportMetaData (filename):
                dlg.Pulse(msg)
            dlg.Destroy()
        else:
            dlg.Destroy()
        
        
Init()        
app = MetaDataEditor()
try:
    #import cProfile
    #cProfile.run( "app.MainLoop()", "/tmp/prov-prof" )
    app.MainLoop()
except orm.ORMError, e:
    wx.MessageBox ( str(e) )
    raise SystemExit

    