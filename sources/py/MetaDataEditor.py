#!/bin/env python
##$Id$
from ProvCon.dbui.database import CFG, Init
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk

import wx
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
        
        self.fieldrecords = orm.RecordList ( fieldinfotable, select=['name'], order="lp" )
        self.fieldrecords.filterfunc = lambda r: r.name not in meta.Table.__special_columns__        
        self.fieldlist = guitk.recordlists.RecordList (self.fieldrecords, self.toplevel)                
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
        print "M ", menu_data.Append (wx.NewId(), "&Export", "Export meta-data to a text file." )
        print "M ", menu_data.Append (wx.NewId(), "&Import", "Import meta-data to a text file." )
        menu.Append ( menu_data, "&Data" )
        self.toplevel.SetMenuBar ( menu )
        
        self.toplevel.Show()
        
        return True

        
Init()        
app = MetaDataEditor()
try:
    #import cProfile
    #cProfile.run( "app.MainLoop()", "/tmp/prov-prof" )
    app.MainLoop()
except orm.ORMError, e:
    wx.MessageBox ( str(e) )
    raise SystemExit

    