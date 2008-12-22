## $Id$
"""
This module implements a complete, user-ready generic form, capable of editing
data in a table in a provisioning-compatible database.

From the MVC point of view, a GenericForm is a View, a form object (IForm) is the Controller
and a Record is the Model.

A generic 
"""
# -*- coding: utf8 -*-

from forms import GenericForm
from navigators import Navigator
from ProvCon.dbui import orm, meta
from ProvCon.func import conditionalmethod, eventcancelled
import wx

__revision__ = "$Revision$"


class InfoPopup (wx.PopupWindow):
    def __init__(self, form, *args, **kwargs):
        wx.PopupWindow.__init__(self, form, *args, **kwargs)
        self.form = form
        self.SetBackgroundColour ( wx.NamedColor ( "yellow" ) )
        self.SetForegroundColour ( wx.NamedColor ( "red" ) )
        self.label = wx.StaticText ( self, label = "***", pos = (10,10) )
        
    def ShowMessage(self, msg, timeout):
        self.label.Label = msg
        sz = self.label.GetBestSize()
        self.SetSize ( ( sz.width + 20, sz.height+20) )
        ppos = self.form.ClientToScreen ( (0,0) )
        psiz = self.form.Size        
        print ppos, psiz
        self.SetPosition ( ( ppos.x + psiz.x / 2 - sz.x / 2, ppos.y + psiz.y / 2 - sz.y / 2) )
        print self.GetPosition()
        self.Popup()
        wx.CallLater ( timeout, lambda self=self: self.Hide() )

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
        wx.Panel.__init__ (self, parent, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL)
        
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
        self.reload = conditionalmethod ( self.form.revert )
        self.new = conditionalmethod ( self.new )
        self.delete = conditionalmethod (self.form.delete )
    
        
        self.on_toolbar_SAVE = self.save
        self.on_toolbar_NEW = self.new
        self.on_toolbar_RELOAD = self.reload
        self.on_toolbar_DEL = self.delete
        
        self.mainsizer = wx.BoxSizer (wx.VERTICAL)
        
        self.toolbarconfig = kwargs.get ( "toolbar", FormToolbar)
        
        #tool bar
        if self.toolbarconfig:
            self.toolbar = self.toolbarconfig(self, **kwargs)
            self.mainsizer.Add ( self.toolbar, flag=wx.EXPAND )
        else:
            self.toolbar = None

        self.status = wx.StaticText ( self )
        self.status.SetFont ( wx.Font ( 8, wx.FONTFAMILY_MAX, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD ) )        
        self.status.ForegroundColour = (122,66,66)
        self.status.SetThemeEnabled (False )
        self.mainsizer.Add ( self.status, flag=wx.EXPAND | wx.ALL, border=5 )
            
        #editor
        self.editor_scrolled_window = wx.ScrolledWindow ( self, style=wx.VSCROLL | wx.TAB_TRAVERSAL )            
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
            
        self.form.register_event_hook ( "request_record_change", self.before_record_change )
        self.form.register_event_hook ( "current_record_modified", self.current_record_modified )
        self.form.register_event_hook ( "current_record_deleted", self.current_record_deleted )
        self.form.register_event_hook ( "current_record_saved", self.current_record_saved )
        self.form.register_event_hook ( "data_loaded", self.data_loaded )

        self.infowindow = InfoPopup(self)
        
    def current_record_modified(self, record, *args):
        self.status.SetLabel ( "wprowadzono zmiany do danych" )
        
    def current_record_deleted ( self, objectid, *args):        
        self.status.SetLabel ( "Rekord usunięty." )
        wx.CallLater ( 2000, lambda self=self: self.status.SetLabel ( "" ) )
        self.navigator.reload(-1)
    
    def current_record_saved ( self, record, wasnew, *args):
        self.status.SetLabel ( "Rekord zapisany." )        
        wx.CallLater ( 2000, lambda self=self: self.status.SetLabel ( "" ) )
        if wasnew:
            if self.navigator:
                self.navigator.reload(record.objectid)
        elif self.navigator:
            self.navigator.reloadsingle ( record.objectid )

    def data_loaded (self, record, *args):
        wx.CallLater ( 1000, lambda self=self: self.status.SetLabel ( "" ) )
    
    def before_record_change(self, record, newid):
        if record._ismodified:
            ask = wx.MessageBox ( "W aktualnym rekordzie są niezapisane dane, czy chcesz je zapisać?", "Uwaga!", wx.YES_NO | wx.CANCEL )        
            if ask == wx.YES:
                self.save()
            elif ask == wx.NO:
                return
            else:
                raise eventcancelled()
                
        
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
        
        if self.navigator and self.navigator.isonnew() and self.toolbar:
            self.toolbar.SetRecordLabel ( self.form.table.title + " : ** NEW RECORD ** " )
        else:
            self.form.setid ( objectid )        
            if self.toolbar:
                self.toolbar.SetRecordLabel ( self.form.table.title + " : " + str(self.form.current) )
    
    def set_navigator(self, navigator):
        self.navigator = navigator
        self.navigator.register_event_hook ( "navigate", self.navigate )                
        self.navigate ( self.navigator.currentid() )
    
    def new(self):
        self.form.new()
        ##FIXME: ugly 'NEW_RECORD' hack!
        self.navigator.navigate ( None )
        