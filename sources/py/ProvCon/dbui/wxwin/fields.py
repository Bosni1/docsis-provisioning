from ProvCon.dbui.abstractui.fields import *
from ProvCon.func.classes import conditionalmethod
import wx

NoneType = type(None)
a = wx.App()

class STYLE:
    INPUT_BG = wx.Color ( 0xdd, 0xdd, 0xff )
    INPUT_FG = wx.Color ( 0x55, 0, 0 )

def SSET (control, **kkw):
    pass
    

    
class Entry:
    ## simple value editors
    class Static(BaseFieldEditor, wx.StaticText):
        def __init__(self, field, parent, *args, **kwargs):
            wx.StaticText.__init__ (self, parent, name=field.path)
            BaseFieldEditor.__init__(self, field, **kwargs)
            

        def set_current_editor_value(self, value):
            self.SetLabel ( str(value) )
        
    
    class Text (BaseFieldEditor, wx.TextCtrl):
        def __init__(self, field, parent, *args, **kwargs):
            wx.TextCtrl.__init__ (self, parent, name=field.path)
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
    
    ## reference editors
    class ComboReference(BaseReferenceEditor, wx.ComboBox):
        def __init__(self, field, parent, *args, **kwargs):
            wx.ComboBox.__init__ (self, parent, 
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
                
    ## array item editors
    class ArrayItemText(BaseArrayItemEditor, wx.TextCtrl):
        def __init__(self, field, parenteditor, idx, parent, *args, **kwargs):
            self.idx = idx
            wx.TextCtrl.__init__ (self, parent, name=field.path + "_" + str(idx) )
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
                return  value 

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

    class ArrayItemStatic(BaseArrayItemEditor, wx.StaticText):
        def __init__(self, field, parenteditor, idx, parent, *args, **kwargs):
            self.idx = idx
            wx.StaticText.__init__ (self, parent, name=field.path + "_" + str(idx) )
            BaseArrayItemEditor.__init__ (self, field, parenteditor, idx, *args, **kwargs)  

        def set_current_editor_value(self, value):
            self.SetLabel(value)
        
        def get_current_editor_value(self):
            return self.GetLabel()

        initialize_value = set_current_editor_value
    
    class ArrayItemCombo(BaseArrayItemEditor, wx.ComboBox):
        def __init__(self, field, parenteditor, idx, parent, *args, **kwargs):
            self.idx = idx
            wx.ComboBox.__init__ (self, parent, name=field.path + "_" + str(idx) )
            BaseArrayItemEditor.__init__ (self, field, parenteditor, idx, *args, **kwargs)  
            
            print "AIC", self.parenteditor, self.parenteditor.recordlist
            if self.parenteditor.recordlist is not None: self.mode = 'record'
            else: self.mode = 'choice'
            print self.mode
            self.obj_idx_hash = {}
            self.obj_idx_hash[None] = self.Append ( "<null>", None )
            self.obj_idx_hash[()] = self.Append ( "<missing>",  () )
            if self.mode == 'record':
                for r in self.parenteditor.recordlist:                                
                    self.obj_idx_hash[r.objectid] = self.Append ( self.parenteditor.reprfunc (r), r )
            else:
                for (val, disp) in self.parenteditor.choices:                
                    self.obj_idx_hash[val] = self.Append ( disp, val )
            print self.obj_idx_hash
            self._on_combo_box = conditionalmethod (self._on_combo_box)
            self.Bind ( wx.EVT_COMBOBOX, self._on_combo_box )
        
        def set_current_editor_value(self, value):
            try:
                if self.mode == 'record': value = int(value)                
                self.Select ( self.obj_idx_hash[value] )
            except KeyError:
                self.Select ( self.obj_idx_hash[()] )
        
        def get_current_editor_value(self):
            val = self.GetClientData ( self.GetSelection() )
            if self.mode == 'record':                
                if val: return record.objectid
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
                                                    style=wx.BU_EXACTFIT)
                self.sizer.Add ( self.buttons['insert'] )
            if 'delete' in self.commands:
                self.buttons['delete'] = wx.Button (self, label="X",
                                                    style=wx.BU_EXACTFIT)
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
            if bbclass: self.sizer.Add ( bbclass ( self, -1, self, insert=True ) )
            
        def resize_editor (self, newsize):
            itemclass = self.get_item_editor_class()     
            bbclass = self.get_button_box_class()
            print self.size, newsize
            for idx in range(self.size):
                item, sizeritem, bb = self.item_rows[idx]                
                item.Hide()
                if bb: bb.Hide()
            
            for idx in range( max(self.size, 0), newsize):
                if idx < len(self.item_rows): continue
                print "creation of", idx
                item = itemclass (self.field, self, idx, self)                
                sizeritem = self.sizer.Add (item, flag=wx.EXPAND)               

                if bbclass:
                    bb = bbclass (self, idx, self, insert=True, delete=True)
                    self.sizer.Add (bb)
                else:
                    bb = None
                    
                self.item_rows.append ( (item, sizeritem, bb) )                    
            
            self.sizer.SetRows ( newsize )                
            for idx in range(newsize):
                item, sizeritem, bb = self.item_rows[idx]
                item.Show()
                if bb: bb.Show()
            
            self.parent.Layout()
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

    