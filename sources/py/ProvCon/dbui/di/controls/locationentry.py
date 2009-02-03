# -*- coding: utf8 -*-

from ProvCon.dbui.abstractui.fields import BaseReferenceEditor
from ProvCon.func import AttrDict
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin import mwx
from functools import partial
from app import APP
import wx, wx.combo

class LocationEntry(BaseReferenceEditor, wx.CollapsiblePane):
    def __init__(self, field, parent, *args, **kwargs):
        from ProvCon.dbui.orm import Record
        BaseReferenceEditor.__init__(self, field, getrecords=False, *args, **kwargs)
        wx.CollapsiblePane.__init__(self, parent, style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)        
        
        self._current = AttrDict()
        
        self._current.city = Record.EMPTY ( "city" )
        self._current.street = Record.EMPTY ( "street" )
        self._current.building = Record.EMPTY ( "building" )
        self._current.location = Record.EMPTY ( "location" )                
        
        self._widgets = AttrDict()
        self._store = AttrDict()
        self._hooks = AttrDict()
        
        pane = self.GetPane()
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._store.city = APP.DataStore.city
        self._widgets.city = mwx.RecordListCombo ( pane, self._store.city )
        self._hooks.city_change = self._widgets.city.register_event_hook ( 
            "current_record_changed", partial(self.ref_record_changed, "city") )
        self._hooks.city_command = self._widgets.city.register_event_hook ( 
            "keyboard_command", partial(self.ref_keyboard_command, "city") )
        sizer.Add ( self._widgets.city, flag=wx.EXPAND)
                
        self._store.street = orm.RecordListFilter ( APP.DataStore.street )
        self._widgets.street = mwx.RecordListCombo ( pane, self._store.street )
        self._hooks.street_change = self._widgets.street.register_event_hook ( 
            "current_record_changed", partial(self.ref_record_changed, "street") )
        self._hooks.street_command = self._widgets.street.register_event_hook ( 
            "keyboard_command", partial(self.ref_keyboard_command, "street") )        
        sizer.Add ( self._widgets.street, flag=wx.EXPAND)
        
        self._store.building = orm.RecordListFilter ( APP.DataStore.building )
        self._widgets.building = mwx.RecordListCombo ( pane, self._store.building )
        self._hooks.building_change = self._widgets.building.register_event_hook ( 
            "current_record_changed", partial(self.ref_record_changed, "building") )
        self._hooks.building_command = self._widgets.building.register_event_hook ( 
            "keyboard_command", partial(self.ref_keyboard_command, "building") )        
        sizer.Add ( self._widgets.building, flag=wx.EXPAND)
        
        self._store.location = orm.RecordListFilter ( APP.DataStore.location )
        self._widgets.location = mwx.RecordListCombo ( pane, self._store.location )
        self._hooks.location_change = self._widgets.location.register_event_hook ( 
            "current_record_changed", partial(self.ref_record_changed, "location") )
        self._hooks.location_command = self._widgets.location.register_event_hook ( 
            "keyboard_command", partial(self.ref_keyboard_command, "location") )        
        sizer.Add ( self._widgets.location, flag=wx.EXPAND)

        btsizer = wx.BoxSizer (wx.HORIZONTAL)
        
        self._widgets.save = wx.Button (pane, size=(-1,30), label="Ustaw" )
        self._widgets.save.Bind (wx.EVT_BUTTON, self.save)
        btsizer.Add (self._widgets.save, 1, flag=wx.EXPAND)
        
        self._widgets.revert = wx.Button (pane, size=(-1,30), label="Przywróć" )
        btsizer.Add (self._widgets.revert, 1, flag=wx.EXPAND)

        sizer.Add (btsizer, flag=wx.EXPAND)
        
        self._widgets.street.Enabled = False
        self._widgets.building.Enabled = False
        self._widgets.location.Enabled = False                    
        
        pane.SetSizer(sizer)    
        
        self.Bind ( wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneToggled)
                
    def OnPaneToggled(self, evt, *args):
        self.Parent.Layout()
        

    def ref_record_changed(self, tbl, record):
        print tbl, record        
        if tbl == "city":
            if record:
                self._widgets.city.SetValue (record._astxt)                
                self._store.street.predicate = lambda r: r.cityid == record.objectid
                self._widgets.street.Enabled = True                
                self._widgets.street.set_null()                
                self._widgets.building.set_null()
            else:
                self._widgets.street.Enabled = False
                self._store.street.predicate = lambda r: False            
            self._widgets.building.Enabled = False
            self._widgets.location.Enabled = False
            self._widgets.save.Enabled = False
        elif tbl == "street":            
            self._widgets.street.SetValue (record._astxt)                
            if record:
                self._store.building.predicate = lambda r: r.streetid == record.objectid
                self._widgets.building.Enabled = True
                self._widgets.building.set_null()
            else:
                self._store.building.predicate = lambda r: False
                self._widgets.building.Enabled = False
            self._widgets.location.Enabled = False
        elif tbl == "building":
            self._widgets.building.SetValue (record._astxt)                
            if record:
                self._store.location.predicate = lambda r: r.buildingid == record.objectid
                self._widgets.location.Enabled = True
            else:
                self._store.location.predicate = lambda r: False
                self._widgets.location.Enabled = False        
        elif tbl == "location":
            self._widgets.location.SetValue (record._astxt)                
            self._current.location = record   
            if record:
                self._widgets.save.Enabled = True
            
    def ref_keyboard_command(self, tbl, key):
        print tbl, key

    def save(self, evt, *args):        
        self.Label = self._current.location._astxt
        self.update_variable()
        
    def set_current_editor_value(self, value):
        loc = self._current.location
        loc.setObjectID (value)                        
        self._widgets.location.Enabled = False
        if loc.hasData:
            self._widgets.location.Enabled = True
            
            self._current.building.setObjectID ( loc.buildingid )
            self._current.street.setObjectID ( self._current.building.streetid )
            self._current.city.setObjectID ( self._current.street.cityid )
            
            self.ref_record_changed ( "city",  self._current.city)
            self.ref_record_changed ( "street",  self._current.street)
            self.ref_record_changed ( "building",  self._current.building)
            self.ref_record_changed ( "location",  self._current.location)
            
            self.Label = loc._astxt
        else:
            self.Label = "(nie ustawiony)"
        
    def get_current_editor_value(self):        
        return self._current.location._objectid
                