from ProvCon.dbui.abstractui.fields import BaseReferenceEditor
from ProvCon.func import AttrDict
import wx

class LocationEntry(BaseReferenceEditor, wx.Panel):
    def __init__(self, field, parent, *args, **kwargs):
        from ProvCon.dbui.orm import Record
        BaseReferenceEditor.__init__(self, field, getrecords=False, *args, **kwargs)
        wx.Panel.__init__(self, parent)        
        
        self._current = AttrDict()

        self._current.location = Record.EMPTY ( "location" )
        self._current.city = Record.EMPTY ( "city" )
        self._current.street = Record.EMPTY ( "street" )
        self._current.building = Record.EMPTY ( "building" )
        
        self._widgets = AttrDict()
        
        self._widgets.L = wx.StaticText (self, label="<LocationEntry>")        
        self._mode = "display"
    
    def set_current_editor_value(self, value):
        self._current.location.setObjectID (value)
        if self._mode == "display":
            self._widgets.L.Label = self._current.location._astxt
        elif self._mode == "edit":
            pass
        
    def get_current_editor_value(self):
        return self._current.location._objectid
        
