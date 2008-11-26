from ProvCon.dbui.abstractui.fields import *
from ProvCon.func.classes import conditionalmethod
import wx

class Field:

    class Static(BaseFieldEditor, wx.StaticText):
        def __init__(self, field, parent, *args, **kwargs):
            BaseFieldEditor.__init__(self, field, **kwargs)
            wx.StaticText.__init__ (self, parent, name=field.path)

        def set_current_editor_value(self, value):
            self.SetLabel ( str(value) )
        
    
    class Text (BaseFieldEditor, wx.TextCtrl):
        def __init__(self, field, parent, *args, **kwargs):
            BaseFieldEditor.__init__(self, field, **kwargs)
            wx.TextCtrl.__init__ (self, parent, name=field.path)
            self._on_text_changed = conditionalmethod (self._on_text_changed)
            self.Bind ( wx.EVT_TEXT, self._on_text_changed )
            
        def set_current_editor_value(self, value):
            self.SetValue ( str(value) )
        
        def get_current_editor_value(self):
            return self.GetValue()
            
        def _on_text_changed(self, event, *args):
            try:
                self._on_text_changed.freeze()
                self.update_variable()
            finally:
                self._on_text_changed.thaw()
    
    class ComboReference(BaseReferenceEditor, wx.ComboBox):
        def __init__(self, field, parent, *args, **kwargs):
            BaseReferenceEditor.__init__(self, field, **kwargs)
            wx.ComboBox.__init__ (self, parent, 
                                  style=wx.CB_READONLY,
                                  name=field.path)            
            self.obj_idx_hash = {}            
            for r in self.records:                
                self.obj_idx_hash[r.objectid] = self.Append ( self.reprfunc (r), r )
            self._on_combo_box = conditionalmethod (self._on_combo_box)
            self.Bind ( wx.EVT_COMBOBOX, self._on_combo_box )
        
        def set_current_editor_value(self, value):
            self.Select ( self.obj_idx_hash[value] )
        
        def get_current_editor_value(self):
            record = self.GetClientData ( self.GetSelection() )
            return record.objectid
        
        def _on_combo_box(self, event, *args):
            try:
                self._on_combo_box.freeze()
                self.update_variable()
            finally:
                self._on_combo_box.thaw()
    class ArrayItem:
        class Text(BaseArrayItem, Field.Text):
            pass
        