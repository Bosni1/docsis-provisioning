from forms import GenericForm
from navigators import Navigator
from ProvCon.dbui import orm, meta
import art
import wx


class CompleteGenericForm(wx.Panel):
    
    def __init__(self, table, parent, **kwargs):
        wx.Panel.__init__ (self, parent, style=wx.SUNKEN_BORDER)
        self.form = orm.Form ( meta.Table.Get ( table ) )        
        self.mainsizer = wx.BoxSizer (wx.VERTICAL)
        
        
        #tool bar
        self.toolbar = wx.ToolBar(self)
        self.toolbar.AddLabelTool(-1, "new", art.TB_NEW )
        self.toolbar.AddLabelTool(-1, "save", art.TB_SAVE )
        self.toolbar.AddLabelTool(-1, "reload", art.TB_RELOAD )
        self.toolbarlabel = wx.StaticText ( self.toolbar, label="toolbar" )
        self.toolbar.AddControl ( self.toolbarlabel )        
        self.mainsizer.Add ( self.toolbar )    
        
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
        self.navigator = Navigator(self)
        self.mainsizer.Add ( self.navigator, flag=wx.EXPAND )
        
        self.SetSizer ( self.mainsizer )
        self.SetSize ( parent.GetSize() )
        #handlers
        self.editor_scrolled_window.Bind ( wx.EVT_SIZE, self.on_resize)         
        self.editor.Bind ( wx.EVT_SIZE, self.on_editor_resize )
        self.navigator.register_event_hook ( "navigate", self.navigate )
        
        #initialization
        self.recordlist = orm.RecordList (self.form.table).reload()
        self.navigator.set_records ( self.recordlist )
        self.navigator.first()

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
        self.toolbarlabel.SetLabel ( str(self.form.current) )
