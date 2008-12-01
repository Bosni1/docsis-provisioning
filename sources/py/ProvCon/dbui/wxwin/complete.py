from forms import GenericForm
from navigators import Navigator
from ProvCon.dbui import orm, meta
from ProvCon.func import conditionalmethod
import wx

class FormToolbar(wx.ToolBar):
    def __init__(self, form, **kkw):        
        wx.ToolBar.__init__ (self, form)
        self.form = form
        
        self.tools = {}        
        import art
        for b in [ "NEW", "DEL", "SAVE", "RELOAD" ]:
            if not kkw.get ( "no_" + b, False):
                wxid = wx.NewId()
                self.tools[wxid] = (b, self.AddLabelTool (wxid, b, art.TB[b] ))
        
        self.Bind (wx.EVT_TOOL, self.command)
        
        self.label = wx.StaticText ( self, label="toolbar" )
        self.AddControl ( self.label )        
        
    def SetRecordLabel(self, label):
        self.label.SetLabel ( label )
        
    def command(self, event):
        toolname, tool = self.tools.get ( event.GetId(), None)
        if tool:
            try:
                getattr(self.form, "on_toolbar_" + toolname) ()
            except AttributeError:
                pass                            
            
        
class CompleteGenericForm(wx.Panel):
    
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__ (self, parent, style=wx.SUNKEN_BORDER)
        
        self.tablename = kwargs.get ( "tablename", None)
        self.table = kwargs.get ( "table", None)
        self.form = kwargs.get ( "form", None )

        if self.tablename:
            self.table = meta.Table.Get ( self.tablename )
        if self.table:
            self.tablename = self.table.name
            self.form = orm.Form ( self.table )
        if self.form:
            self.table = self.form.table
            self.tablename = self.table.name

        self.save = conditionalmethod ( self.form.save )
        self.reload = conditionalmethod ( self.form.reload )
        self.new = conditionalmethod ( self.form.new )
        self.delete = conditionalmethod (self.form.delete )
        
        self.on_toolbar_SAVE = self.save
        self.on_toolbar_NEW = self.new
        self.on_toolbar_RELOAD = self.reload
        self.on_toolbar_DEL = self.delete
        
        self.mainsizer = wx.BoxSizer (wx.VERTICAL)
        
        self.toolbarconfig = kwargs.get ( "toolbar", FormToolbar)
        
        #tool bar
        if self.toolbarconfig:
            self.toolbar = self.toolbarconfig(self)
            self.mainsizer.Add ( self.toolbar, flag=wx.EXPAND )
        else:
            self.toolbar = None
            
        #editor
        self.editor_scrolled_window = wx.ScrolledWindow ( self, style=wx.VSCROLL )            
        self.editor = GenericForm ( self.form, self.editor_scrolled_window )  
        self.editor.create_widget()
        self.scrolledsizer = wx.BoxSizer()
        self.scrolledsizer.Add ( self.editor, flag=wx.EXPAND )        
        self.editor_scrolled_window.SetSizer ( self.scrolledsizer )
        self.editor_scrolled_window.SetScrollbars(20,20,50,50)        
        self.mainsizer.Add ( self.editor_scrolled_window, 1, flag=wx.EXPAND )
        
        #navigator
        navigator_config = kwargs.get ( "navigator", Navigator )
        navigator_options = kwargs.get ( "navigatoroptions", {} )
        if navigator_config:
            navigator = navigator_config(self, **navigator_options)
            self.recordlist = orm.RecordList (self.form.table).reload()
            navigator.set_records ( self.recordlist )
            navigator.first()
            self.mainsizer.Add ( navigator, flag=wx.EXPAND )            
        else:
            navigator = None
            
        self.SetSizer ( self.mainsizer )
        self.SetSize ( parent.GetSize() )
        #handlers
        self.editor_scrolled_window.Bind ( wx.EVT_SIZE, self.on_resize)         
        self.editor.Bind ( wx.EVT_SIZE, self.on_editor_resize )

        if navigator:
            self.set_navigator ( navigator )

    def on_editor_resize(self, event, *args):
        self.editor_scrolled_window.SetVirtualSize ( event.GetSize() )        
        event.Skip()
        
    def on_resize(self, event, *args):
        w, h = self.editor_scrolled_window.GetSize()        
        ew, eh = self.editor.GetSize()
        self.editor.SetMinSize ( ( w-20, eh ) )        
        self.editor_scrolled_window.SetVirtualSize ( (ew, eh) )
        event.Skip()
    
    def navigate (self, objectid):
        self.form.setid ( objectid )        
        if self.toolbar:
            self.toolbar.SetRecordLabel ( str(self.form.current) )
    
    def set_navigator(self, navigator):
        self.navigator = navigator
        self.navigator.register_event_hook ( "navigate", self.navigate )                
        self.navigate ( self.navigator.currentid() )
        