# -*- coding: utf8 -*-

from ProvCon.dbui.abstractui.fields import BaseReferenceEditor
from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
import wx, wx.combo

class LocationEntry(BaseReferenceEditor, wx.CollapsiblePane):
    def __init__(self, field, parent, *args, **kwargs):
        from ProvCon.dbui.orm import Record
        BaseReferenceEditor.__init__(self, field, getrecords=False, *args, **kwargs)
        wx.CollapsiblePane.__init__(self, parent, style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)        
        
        self._current = AttrDict()

        self._current.location = Record.EMPTY ( "location" )        
        self._current.city = Record.EMPTY ( "city" )
        self._current.street = Record.EMPTY ( "street" )
        self._current.building = Record.EMPTY ( "building" )
                
        
        self._widgets = AttrDict()
        pane = self.GetPane()
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._widgets.city = wx.TextCtrl ( pane, value = "")
        sizer.Add ( self._widgets.city, flag=wx.EXPAND)
        
        self._widgets.street = wx.TextCtrl ( pane, value = "")
        sizer.Add ( self._widgets.street, flag=wx.EXPAND)
        
        self._widgets.building = wx.TextCtrl ( pane, value = "")
        sizer.Add ( self._widgets.building, flag=wx.EXPAND)
        
        self._widgets.location = wx.TextCtrl ( pane, value = "")
        sizer.Add ( self._widgets.location, flag=wx.EXPAND)
        
        pane.SetSizer(sizer)    
        
        self.Bind ( wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneToggled)
                
    def OnPaneToggled(self, evt, *args):
        #self.Collapse(self.IsCollapsed())
        #self.Layout()
        #print self.IsCollapsed()
        #self.widgets
        self.Parent.Layout()
        
        
    def set_current_editor_value(self, value):
        self._current.location.setObjectID (value)                
        self._widgets.location.Enabled = False
        if self._current.location.hasData:
            self._widgets.location.Enabled = True
            self._widgets.location.Value = self._current.location.number
        
        self.Label = self._current.location._astxt
        
    def get_current_editor_value(self):
        return self._current.location._objectid
        
