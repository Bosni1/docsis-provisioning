from ProvCon.dbui.abstractui.forms import BaseForm
from fields import Field as EntryWidgets
import wx

class GenericForm(BaseForm, wx.Panel):
    
    def __init__(self, form, parent, *args, **kwargs):
        BaseForm.__init__( self, form, *args, **kwargs )
        wx.Panel.__init__( self, parent, style=wx.VSCROLL )        
        
    def _build_ui(self):
        self.sizer = wx.FlexGridSizer( self.form.table.fieldCount() + 1, 3, 1, 0 )        
        self.sizer.AddGrowableCol (1)
        for f in self.form.table:
            self.sizer.Add ( wx.StaticText ( self, label = f.name ) )
            self.sizer.Add ( self._create_field_editor (f, self), flag=wx.EXPAND)
            self.sizer.Add ( wx.StaticText ( self, label = "<tb>" ) )
        cmd = wx.Button( self, label="CMD" )      
        self.sizer.Add ( cmd )
        cmd.Bind ( wx.EVT_BUTTON, self.cmd )
        self.SetSizer (self.sizer)
    
    def _create_default_field_editor (self, field, parent=None, **kwargs):
        editor_class_name = "Text"
        options = {}
        if field.isarray:
            if field.arrayof:
                editor_class_name = "ArrayCombo"
                options['recordlist'] = []
            else:
                editor_class_name = "Array" + field.editor_class
                if not hasattr(EntryWidgets, editor_class_name):
                    editor_class_name = "ArrayText"
        elif field.reference:
            editor_class_name = field.editor_class + "Reference"
            if not hasattr(EntryWidgets, editor_class_name):
                editor_class_name = "ComboReference"
        else:
            editor_class_name = field.editor_class
            
        try:
            editor_class = getattr(EntryWidgets, editor_class_name)
        except AttributeError:
            editor_class = EntryWidgets.Text        
        
        editor = editor_class (field, parent, variable = self.form[field.name], **options )        
        return editor

    def cmd(self, event, *args):
        print self.form.current.PP_TABLE
        self.form.setid ( 24 )
        
