from ProvCon.dbui.abstractui.fields import *
from ProvCon.func.classes import conditionalmethod
import wx
import mwx

NoneType = type(None)
    
class Entry:
    ## simple value editors
    class Static(BaseFieldEditor, mwx.StaticText):
        def __init__(self, field, parent, *args, **kwargs):
            mwx.StaticText.__init__ (self, parent, name=field.path)
            BaseFieldEditor.__init__(self, field, **kwargs)
            

        def set_current_editor_value(self, value):
            self.SetLabel ( self.field.val_py2txt(value) )
                
    
    class Text (BaseFieldEditor, mwx.TextCtrl):
        def __init__(self, field, parent, *args, **kwargs):
            config = kwargs.get ( "config", {})            
            mwx.TextCtrl.__init__ (self, parent, name=field.path, **config)
            BaseFieldEditor.__init__(self, field, **kwargs)
            self._on_text_changed = conditionalmethod (self._on_text_changed)
            self.Bind ( wx.EVT_TEXT, self._on_text_changed )
            self.datatype = NoneType
            
        def set_current_editor_value(self, value):
            self.datatype = type(value)
            if self.datatype == NoneType:
                self.SetValue ( '' )
            else:
                self.SetValue ( self.field.val_py2txt(value) )
        
        def get_current_editor_value(self):
            value = self.GetValue()
            if self.datatype == NoneType and len(value) == 0:
                return None
            else:
                return self.field.val_txt2py ( value )
            
        def _on_text_changed(self, event, *args):
            try:
                self._on_text_changed.freeze()
                self.update_variable()
            finally:
                self._on_text_changed.thaw()
    
    class Memo(Text):
        def __init__(self, *args, **kwargs):            
            kwargs['config'] =  { 'style' : wx.TE_MULTILINE}
            Entry.Text.__init__ (self, *args, **kwargs)
            
            self.SetMinSize ( (10, 100) )
        
    class Boolean(BaseFieldEditor, mwx.CheckBox):
        def __init__(self, field, parent, *args, **kwargs):
            mwx.CheckBox.__init__ (self, parent, 
                                   style = wx.CHK_3STATE,
                                   name=field.path)
            BaseFieldEditor.__init__(self, field, **kwargs)
            self._on_checked = conditionalmethod ( self._on_checked )
            self.Bind ( wx.EVT_CHECKBOX, self._on_checked )
            self.datatype = NoneType
            
        def set_current_editor_value(self, value):
            self.datatype = type(value)
            if self.datatype == NoneType:
                self.Set3StateValue ( wx.CHK_UNDETERMINED )
            elif value:
                self.Set3StateValue ( wx.CHK_CHECKED )
            else:
                self.Set3StateValue ( wx.CHK_UNCHECKED )
        
        def get_current_editor_value(self):
            value = self.Get3StateValue()
            if value == wx.CHK_UNDETERMINED:
                return None
            elif value == wx.CHK_CHECKED:
                return True
            else:
                return False
            
        def _on_checked(self, event, *args):
            try:
                self._on_checked.freeze()
                self.update_variable()
            finally:
                self._on_checked.thaw()
        
    class Choice  (BaseFieldEditor, mwx.ComboBox):
        def __init__(self, field, parent, *args, **kwargs):
            mwx.ComboBox.__init__(self, parent,
                                  style=wx.CB_READONLY,
                                  name=field.path)
            BaseFieldEditor.__init__(self, field, **kwargs)
            self.val_idx_hash = {}
            self.val_idx_hash[None] = self.Append ( '<null>', None )
            for val, disp in field.choices:
                self.val_idx_hash[val] = self.Append ( disp, val )
            self._on_combo_box = conditionalmethod ( self._on_combo_box )
            self.Bind (wx.EVT_COMBOBOX, self._on_combo_box )

        def set_current_editor_value(self, value):
            self.Select ( self.val_idx_hash[value] )
        
        def get_current_editor_value(self):
            return self.GetClientData ( self.GetSelection() )            
        
        def _on_combo_box(self, event, *args):
            try:
                self._on_combo_box.freeze()                
                self.update_variable()
            finally:
                self._on_combo_box.thaw()    
        
    ##choosers
    class ListReference(BaseReferenceEditor, mwx.ListReference):
        def __init__(self, field, parent, *args, **kwargs):            
            BaseReferenceEditor.__init__(self, field, **kwargs)
            mwx.ListReference.__init__(self, parent, name=field.path)                        
            self.popup_ctrl.reprfunc = self.reprfunc
            self.popup_ctrl.SetRecords (self.records)        
            
        def set_current_editor_value (self, value):
            self.popup_ctrl.CurrentOID = value

        def get_current_editor_value (self):
            return self.popup_ctrl.CurrentOID
                
    ## reference editors
    class ComboReference(BaseReferenceEditor, mwx.ComboReference):
        def __init__(self, field, parent, *args, **kwargs):
            mwx.ComboReference.__init__ (self, parent, 
                                  style=wx.CB_READONLY,
                                  name=field.path)            
            BaseReferenceEditor.__init__(self, field, **kwargs)
            self.obj_idx_hash = {}            
            self.obj_idx_hash[None] = self.Append ( "<null>", None )
            for r in self.records:                
                self.obj_idx_hash[r.objectid] = self.Append ( self.reprfunc (r), r )
            self._on_combo_box = conditionalmethod (self._on_combo_box)
            self.Bind ( wx.EVT_COMBOBOX, self._on_combo_box )
        
        def set_current_editor_value(self, value):
            self.Select ( self.obj_idx_hash[value] )
        
        def get_current_editor_value(self):
            record = self.GetClientData ( self.GetSelection() )            
            if record:
                return record.objectid
            else:
                return None
        
        def _on_combo_box(self, event, *args):
            try:
                self._on_combo_box.freeze()                
                self.update_variable()
            finally:
                self._on_combo_box.thaw()    
                
    class StaticReference(BaseReferenceEditor, mwx.StaticReference):
        def __init__(self, field, parent, *args, **kwargs):
            mwx.StaticText.__init__ (self, parent, 
                                  style=wx.CB_READONLY,
                                  name=field.path)            
            BaseReferenceEditor.__init__(self, field, getrecords=False, **kwargs)
            from ProvCon.dbui.orm import Record
            self.referenced_record = Record.EMPTY ( field.reference.name )
        
        def set_current_editor_value(self, value):
            if value is None:
                self.SetLabel ( "<null>" )
            else:
                self.referenced_record.setObjectID ( value ) 
                self.SetLabel ( self.reprfunc ( self.referenced_record ) )
                
    ## array item editors
    class ArrayItemText(BaseArrayItemEditor, mwx.TextCtrl):
        def __init__(self, field, parenteditor, idx, parent, *args, **kwargs):
            self.idx = idx
            mwx.TextCtrl.__init__ (self, parent, name=field.path + "_" + str(idx) )
            BaseArrayItemEditor.__init__ (self, field, parenteditor, idx, *args, **kwargs)  
            self._on_text_changed = conditionalmethod (self._on_text_changed)
            self.Bind ( wx.EVT_TEXT, self._on_text_changed )
            self.datatype = NoneType
            
        def set_current_editor_value(self, value):
            self.datatype = type(value)
            if self.datatype == NoneType:
                self.SetValue ( '' )
            else:
                self.SetValue (value)

        
        def get_current_editor_value(self):
            value = self.GetValue()
            if self.datatype == NoneType and len(value) == 0:
                return None
            else:
                return value 

        def initialize_value(self, value):
            try:
                self._on_text_changed.freeze()
                self.set_current_editor_value (value)
            finally:
                self._on_text_changed.thaw()
                
        def _on_text_changed(self, event, *args):
            try:
                self._on_text_changed.freeze()
                self.update_variable()
            finally:
                self._on_text_changed.thaw()

    class ArrayItemStatic(BaseArrayItemEditor, mwx.StaticText):
        def __init__(self, field, parenteditor, idx, parent, *args, **kwargs):
            self.idx = idx
            mwx.StaticText.__init__ (self, parent, name=field.path + "_" + str(idx) )
            BaseArrayItemEditor.__init__ (self, field, parenteditor, idx, *args, **kwargs)  

        def set_current_editor_value(self, value):
            self.SetLabel(value)
        
        def get_current_editor_value(self):
            return self.GetLabel()

        initialize_value = set_current_editor_value
    
    class ArrayItemCombo(BaseArrayItemEditor, mwx.ComboBox):
        def __init__(self, field, parenteditor, idx, parent, *args, **kwargs):
            self.idx = idx
            mwx.ComboBox.__init__ (self, parent, name=field.path + "_" + str(idx) )
            BaseArrayItemEditor.__init__ (self, field, parenteditor, idx, *args, **kwargs)  
                        
            if self.parenteditor.recordlist is not None: self.mode = 'record'
            else: self.mode = 'choice'            
            self.obj_idx_hash = {}
            self.obj_idx_hash[None] = self.Append ( "<null>", None )
            self.obj_idx_hash[()] = self.Append ( "<missing>",  () )
            if self.mode == 'record':
                for r in self.parenteditor.recordlist:                                
                    self.obj_idx_hash[r.objectid] = self.Append ( self.parenteditor.reprfunc (r), r )
            else:
                for (val, disp) in self.parenteditor.choices:                
                    self.obj_idx_hash[val] = self.Append ( disp, val )
            
            self._on_combo_box = conditionalmethod (self._on_combo_box)
            self.Bind ( wx.EVT_COMBOBOX, self._on_combo_box )
        
        def set_current_editor_value(self, value):
            try:
                if self.mode == 'record' and value is not None: value = int(value)                
                self.Select ( self.obj_idx_hash[value] )
            except KeyError:
                self.Select ( self.obj_idx_hash[()] )
        
        def get_current_editor_value(self):
            val = self.GetClientData ( self.GetSelection() )
            print self, "get_current_ed_val", val
            if self.mode == 'record':                
                if val: return val.objectid
            elif self.mode == 'choice':
                return val
            return None

        def initialize_value(self, value):
            try:
                self._on_combo_box.freeze()
                self.set_current_editor_value (value)
            finally:
                self._on_combo_box.thaw()
        
        def _on_combo_box(self, event, *args):
            try:
                self._on_combo_box.freeze()
                self.update_variable()
            finally:
                self._on_combo_box.thaw()
        
    ## array button boxes
    class StandardArrayItemButtonBox (BaseArrayItemButtonBox, wx.Panel):
        def __init__(self, arrayeditor, idx, parent, **kkw):
            wx.Panel.__init__(self, parent)
            BaseArrayItemButtonBox.__init__(self, arrayeditor, idx, **kkw)            
            self.sizer = wx.GridSizer(1,2)
            self.buttons = {}
            if 'insert' in self.commands:
                self.buttons['insert'] = wx.Button (self, label="+",
                                                    style=wx.BU_EXACTFIT|wx.TAB_TRAVERSAL)
                self.sizer.Add ( self.buttons['insert'] )
            if 'delete' in self.commands:
                self.buttons['delete'] = wx.Button (self, label="X",
                                                    style=wx.BU_EXACTFIT|wx.TAB_TRAVERSAL)
                self.sizer.Add ( self.buttons['delete'] )
            
            for b in self.buttons:                       
                self.buttons[b].SetSize ( wx.Size( w = 5, h = 5 ) )
                if hasattr(self, "command_" + b):
                    self.buttons[b].Bind ( wx.EVT_BUTTON, getattr(self, "command_" + b) )
            
            self.SetSizer ( self.sizer ) 
            
                
    ## array editors    
    class BaseArray (wx.Panel):
        def __init__(self, parent, *args, **kwargs):
            wx.Panel.__init__(self, parent,
                              style=wx.SUNKEN_BORDER)
            
            self.parent = parent
            self.SetBackgroundColour ( wx.WHITE )
            columns = 1
            bbclass = self.get_button_box_class()
            if bbclass: columns += 1
            
            self.sizer = wx.FlexGridSizer (1, columns)     
            self.sizer.AddGrowableCol (0)
            self.SetSizer (self.sizer)
            
            self.item_rows = []
            self.sizer.Add ( wx.StaticLine ( self ), wx.EXPAND )
            if bbclass: 
                self.topinsertbb = bbclass ( self, -1, self, insert=True )
                self.sizer.Add ( self.topinsertbb )
            
        def resize_editor (self, newsize):
            itemclass = self.get_item_editor_class()     
            bbclass = self.get_button_box_class()
            
            for idx in range(self.size):
                item, sizeritem, bb = self.item_rows[idx]                
                item.Hide()
                if bb: bb.Hide()
            
                
            for idx in range( max(self.size, 0), newsize):
                if idx < len(self.item_rows): continue
                
                item = itemclass (self.field, self, idx, self)                
                sizeritem = self.sizer.Add (item, flag=wx.EXPAND)                               
                #sizeritem = self.sizer.Insert (2*idx, item, flag=wx.EXPAND)

                if bbclass:
                    bb = bbclass (self, idx, self, insert=True, delete=True)
                    self.sizer.Add (bb)
                    #self.sizer.Insert (2*idx+1, bb)
                else:
                    bb = None
                    
                self.item_rows.append ( (item, sizeritem, bb) )                    
                            
            for idx in range(newsize):
                item, sizeritem, bb = self.item_rows[idx]
                item.Show()
                if bb: bb.Show()                        

            self.parent.Layout()
            self.parent.Fit()
            self.size = newsize
            
        def set_current_editor_item_value(self, idx, value):
            item,_,_ = self.item_rows[idx]
            item.initialize_value ( value )
    
        def get_current_editor_value(self):
            print "get_current_editor"
    
        def get_current_editor_item_value(self, idx):
            print "get_current_editor_item", idx
            
    class ArrayText (BaseArray, ConcreteBaseArrayEditor(ArrayItemText, StandardArrayItemButtonBox)):
        def __init__(self, field, parent, *args, **kwargs):
            BaseArrayEditor.__init__(self, field, *args, **kwargs)
            Entry.BaseArray.__init__(self, parent)
            
    class ArrayCombo (BaseArray, ConcreteBaseArrayEditor(ArrayItemCombo, StandardArrayItemButtonBox)):
        def __init__(self, field, parent, *args, **kwargs):            
            BaseArrayEditor.__init__(self, field, *args, **kwargs)
            Entry.BaseArray.__init__(self, parent)

    