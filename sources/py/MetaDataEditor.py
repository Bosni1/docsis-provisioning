#!/bin/env python
from ProvCon.dbui.database import CFG
from ProvCon.dbui import meta, orm
from ProvCon.dbui import wxwin as guitk

import wx



#from wx.lib import scrolledpanel as scrolled

class FieldListCommandBuilder:
    __commands__ = [ "cmd1", "cmd2", "cmd3" ]
    __imagelist__ = None
    __images__ = {}
    def __init__(self):
        pass
        
    def get_image_list (self):
        if not self.__imagelist__:
            import ProvCon.dbui.wxwin.art as art
            self.__imagelist__ = wx.ImageList (10, 10)
            self.__images__["cmd1"] = self.__imagelist__.Add ( art.TB_DEL )
            self.__images__["cmd2"] = self.__imagelist__.Add ( art.TB_DEL )
            self.__images__["cmd3"] = self.__imagelist__.Add ( art.TB_DEL )            
        return self.__imagelist__
    
    def get_commands_count(self, objecttype="field_info"):
        return 3
    
    def get_command_items (self, record):
        for c in self.__commands__:
            yield c, self.__images__[c]
        

class MetaDataEditor(wx.App):
    def OnInit(self):
        
        self.toplevel = wx.Frame (None, title="Provisioning meta-data editor", size=(1100,800))

        sizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        lsizer = wx.BoxSizer(wx.VERTICAL)
        
        ##table info editor
        self.tableeditor = guitk.complete.CompleteGenericForm ( self.toplevel, tablename="table_info",
                                                                navigator = False)
        lsizer.Add (self.tableeditor, 4, flag=wx.EXPAND)
        
        
        fieldinfotable = meta.Table.Get ( "field_info" )
        
        self.fieldrecords = orm.RecordList ( fieldinfotable, select=['name'], order="lp" )
        self.fieldrecords.filterfunc = lambda r: r.name not in meta.Table.__special_columns__        
        self.fieldlist = guitk.recordlists.RecordList (self.fieldrecords, self.toplevel, commandbuilder=FieldListCommandBuilder())                
        self.fieldlist.bind_to_form ( "classid", self.tableeditor.form )
        
        lsizer.Add (self.fieldlist, 2, flag=wx.EXPAND)
                               
        rsizer = wx.BoxSizer (wx.VERTICAL)
        self.fieldeditor = guitk.complete.CompleteGenericForm ( self.toplevel, table = fieldinfotable,
                                                                navigator = False)
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
        self.toplevel.Show()
        
        return True

        
        
app = MetaDataEditor()
app.MainLoop()
    