from ProvCon.dbui.abstractui.forms import BaseForm
from ProvCon.dbui.orm import RecordList
from ProvCon.dbui.meta import Table
from fields import Entry as EntryWidgets
import wx

class GenericForm(BaseForm, wx.Panel):
    
    def __init__(self, form, parent, *args, **kwargs):
        BaseForm.__init__( self, form, *args, **kwargs )
        wx.Panel.__init__( self, parent, style=wx.RAISED_BORDER )                
        
    def _build_ui(self):
        self.sizer = wx.FlexGridSizer( self.form.table.fieldCount() + 1, 2, 1, 0 )                        
        self.sizer.AddGrowableCol (1)
        for f in filter(lambda f: f.name not in Table.__special_columns__, self.form.table):
            self.sizer.Add ( wx.StaticText ( self, label = f.name ) )
            self.sizer.Add ( self._create_field_editor (f, self), 10, flag=wx.EXPAND)
        
        self.SetSizer (self.sizer)
        self.SetAutoLayout(1)
        
        #self.Bind ( wx.EVT_SIZE, self.resize )

    def resize(self, e):
        e.Skip()
        
        
    def _create_default_field_editor (self, field, parent=None, **kwargs):
        editor_class_name = "Text"
        options = {}
        if field.isarray:
            if field.arrayof:
                editor_class_name = "ArrayCombo"
                options['recordlist'] = RecordList ( field.arrayof ).reload()           
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
        #editor.Bind ( wx.EVT_SIZE, self.resize )
        return editor

        
