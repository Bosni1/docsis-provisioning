##$Id$
from ProvCon.dbui.abstractui.forms import BaseForm
from ProvCon.dbui.orm import RecordList
from ProvCon.dbui.meta import Table
from fields import Entry as EntryWidgets
import wx

__revision__ = "$Revision$"


class GenericForm(BaseForm, wx.Panel):
    
    def __init__(self, form, parent, *args, **kwargs):
        BaseForm.__init__( self, form, *args, **kwargs )
        wx.Panel.__init__( self, parent, style=wx.TAB_TRAVERSAL)
        self.excluded_fields = kwargs.get ( "excluded", [] )
        
    def _build_ui(self):
        self.sizer = wx.FlexGridSizer( self.form.table.fieldCount() + 1 - len(self.excluded_fields) + len(self.form.extra_fields), 3, 1, 0 )                                
        self.sizer.AddGrowableCol (1)
        for f in filter(lambda f: f.name not in Table.__special_columns__, self.form.table):   
            if f.name in self.excluded_fields: continue
            label = wx.StaticText ( self, label = f.label )                        
            self.sizer.Add ( label, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=20 )
            self.sizer.Add ( self._create_field_editor (f, self), 20, flag=wx.EXPAND)
            self.sizer.AddSpacer ( 20 )
            
        for f in self.form.extra_fields:
            label = wx.StaticText (self, label = f.label )
            self.sizer.Add ( label, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=20 )
            self.sizer.Add ( f.create_editor(self, self.form), 20, flag=wx.EXPAND)
            self.sizer.AddSpacer ( 20 )
            
        self.SetSizer (self.sizer)
        self.SetAutoLayout(1)
        
        #self.Bind ( wx.EVT_SIZE, self.resize )

    def resize(self, e):
        e.Skip()
                
    def _create_default_field_editor (self, field, parent=None, **kwargs):
        from app import APP
        editor_class_name = field.editor_class
        default_class = EntryWidgets.Text
        options = {}
        prefix = ''
        suffix = ''
        if field.isarray:
            if field.arrayof:
                editor_class_name = "List"
                prefix = "Array"
                options['recordlist'] = RecordList ( field.arrayof ).reload()           
                default_class = EntryWidgets.ArrayCombo
            else:
                prefix = 'Array'
                default_class = EntryWidgets.ArrayText
        elif field.reference:
            suffix = 'Reference'
            default_class = EntryWidgets.ListReference
        
        wanted_class_name = prefix + editor_class_name + suffix
        print field, field.editor_class, wanted_class_name
        
        if hasattr (EntryWidgets,wanted_class_name ):
            editor_class = getattr(EntryWidgets, wanted_class_name)
        elif APP.getExtraDataEditor (wanted_class_name):
            editor_class = APP.getExtraDataEditor (wanted_class_name)
        else:
            editor_class = default_class
            
        editor = editor_class (field, parent, variable = self.form.getvar(field.name), **options )        
        return editor

class ScrolledGenericForm(wx.ScrolledWindow):
    
    def __init__(self, form, parent, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, parent)
        
        self.genericform = GenericForm(form, self, *args, **kwargs)
        self.genericform.create_widget()
        self.sizer = wx.BoxSizer()        
        self.sizer.Add ( self.genericform, flag=wx.EXPAND)
        self.SetSizer (self.sizer)
        self.SetScrollbars(20,20,50,50)        
        
        self.Bind ( wx.EVT_SIZE, self.on_resize)        
        self.genericform.Bind ( wx.EVT_SIZE, self.on_editor_resize )

    def on_editor_resize(self, event, *args):
        self.SetVirtualSize ( event.GetSize() )        
        event.Skip()
        
    def on_resize(self, event, *args):
        w, h = self.GetSize()        
        ew, eh = self.genericform.GetSize()
        self.genericform.SetMinSize ( ( w-20, eh ) )        
        self.genericform.SetVirtualSize ( (ew, eh) )
        event.Skip() 
        
class GenericFormDialog(wx.Dialog):
    def __init__(self, parent, form, title, **kwargs):
        
        self.form = form
        pre = wx.PreDialog()
        #pre.SetExtraStyle(...)
        pre.Create (parent, -1, title, wx.DefaultPosition, wx.Size(600, 500)) 
        self.PostCreate(pre)
        
        sizer = wx.BoxSizer (wx.VERTICAL)        
        
        sgform = ScrolledGenericForm (form, self, **kwargs)
        sizer.Add (sgform, 10, flag=wx.EXPAND)

        btsizer = wx.BoxSizer (wx.HORIZONTAL)
        btsave = wx.Button(self, label="Zapisz")
        btcancel = wx.Button(self, label="Anuluj")

        btsizer.Add (btsave, 1, flag=wx.EXPAND)
        btsizer.Add (btcancel, 1, flag=wx.EXPAND)
        
        sizer.Add (btsizer, flag=wx.EXPAND)
                
        self.SetSizer (sizer)        

    def Load(self, objectid):
        self.form.setid (objectid)
    
    def Edit(self):        
        self.ShowModal()
        
    def New(self):
        self.form.new ()

def GenerateEditorDialog ( tablename, title, excluded=[], extra=[] ):
    from ProvCon.dbui.orm import Form
    class _EditorDialog(GenericFormDialog):
        def __init__(self, parent, **kw):
            form = Form ( Table.Get ( tablename ), extra_fields = extra  )
            GenericFormDialog.__init__( self, parent, form, title, **kw )
    _EditorDialog.__name__ = "GenericFormDialog_" + tablename
    return _EditorDialog
        
        
