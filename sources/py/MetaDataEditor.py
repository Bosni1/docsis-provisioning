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
        import cPickle
        ti_rs = CFG.CX.query ( "SELECT * FROM {0}.table_info".format (CFG.DB.SCHEMA) ).dictresult()
        fi_rs = CFG.CX.query ( "SELECT * FROM {0}.field_info".format (CFG.DB.SCHEMA) ).dictresult()
        export = { 'table' : ti_rs, 'field' : fi_rs }        
        
        dlg = wx.FileDialog(self.toplevel, message="Export to file...",
                            style=wx.SAVE,
                            wildcard = "Meta-Data backup (*.md) |*.md|"  \
                                       "All files (*.*)|*.*" )
        if dlg.ShowModal() == wx.ID_OK:
            f = open(dlg.GetPath(), 'w')
            cPickle.dump(export, f)
            f.close()
            
        dlg.Destroy()
                                    
    
    def ImportData(self, *args):
        import cPickle
        dlg = wx.FileDialog(self.toplevel, message="Import from file...",
                            style=wx.OPEN,
                            wildcard = "Meta-Data backup (*.md) |*.md|"  \
                                       "All files (*.*)|*.*" )
        if dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()            
            export = cPickle.load ( open(dlg.GetPath(), 'r') )            
            
        
            dlg = wx.ProgressDialog ("Import danych z " + dlg.GetPath(), "Importowanie...",
                                     parent = self.toplevel)
                                     
            dlg.Show()

            dlg.Pulse()
            current_ti = CFG.CX.query ( "SELECT objectid, schema || '.' || name as path FROM {0}.table_info".format(CFG.DB.SCHEMA) ).dictresult()
            dlg.Pulse()
            current_fi = CFG.CX.query ( "SELECT objectid, classid as parent, path FROM {0}.field_info".format(CFG.DB.SCHEMA) ).dictresult()
            
            
            cTI = {}
            cFI = {}
            for t in current_ti: cTI[t['path']] = t['objectid']
            for f in current_fi: cFI[f['path']] = f['objectid']

            oTI = {}
            oFI = {}            
            o_idTI = {}
            o_idFI = {}            

            ti = export['table']
            fi = export['field']
            
            for t in ti: 
                o_idTI[t['objectid']] = t
                oTI[t['schema'] + "." + t['name']] = t
                
            for f in fi: 
                o_idFI[t['objectid']] = f
                oFI[f['path']] = f
                
            cTable = orm.Record.EMPTY("table_info")
            cField = orm.Record.EMPTY("field_info")
            
            direct_copy = [ "label", "title", "info", "pprint_expression",
                            "disabledfields", "recordlistpopup",
                            "knownflags", "knownparams","hasevents",
                            "hasnotes","excludedfields", 
                            "txtexpression", "recordlisttoolbox" ]
            for t in cTI:
                dlg.Pulse(t)
                ot = oTI[t]
                cTable.setObjectID ( cTI[t] )

                for cn in direct_copy:                    
                    fld = cTable._table[cn]
                    val = ot[cn]
                    if fld.isarray: 
                        if val: val = "array:" + val
                        else: val = '' 
                        val = fld.val_txt2py(val)                    
                    print cn, val
                    cTable.setFieldValue(cn, val)
                                
                cTable.write()
                
            
            direct_copy = [ "label", "length", "choices", "ndims",
                            "reference_editable", "pprint_fkexpression",
                            "required", "protected", "nullable",
                            "quickhelp", "helptopic", "info",
                            "editor_class", "editor_class_params" ]
            #direct_copy.remove("choices")
            #direct_copy.remove('editor_class_params')
            for f in cFI:                
                try:
                    of = oFI[f]
                except KeyError:
                    continue
                dlg.Pulse(f)
                cField.setObjectID (cFI[f])
                
                for cn in direct_copy:                    
                    fld = cField._table[cn]                    
                    val = of[cn]
                    if fld.isarray: 
                        if val: val = "array:" + val
                        else: val = '' 
                        val = fld.val_txt2py(val)                    
                    cField.setFieldValue(cn, val)
                
                if of["arrayof"]:    
                    oldt = o_idTI [ of["arrayof"] ]
                    oldtpath = oldt["schema"] + "." + oldt["name"]
                    cField.arrayof = cTI[ oldtpath ]                                                        

                cField.write()
                
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

    