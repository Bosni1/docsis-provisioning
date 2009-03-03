##$Id:$
# -*- coding: utf8 -*-
from ProvCon.func import AttrDict, partial
from ProvCon.dbui import orm, meta
from ProvCon.dbui.wxwin.forms import GenericForm, ScrolledGenericForm, GenerateEditorDialog
from ProvCon.dbui.wxwin import recordlists as rl, mwx, forms
from ProvCon.dbui.wxwin.fields import Entry
from app import APP
import wx
import wx.aui
import wx.lib.scrolledpanel as scroll
import wx.lib.rcsizer as rcs

class DeviceMain(wx.Panel):
    
    def __init__(self, parent, *args):
        from ProvCon.dbui.di import rDevice
        wx.Panel.__init__(self, parent, *args)
        
        self.form = AttrDict()
        self.table = AttrDict()
        self.editor = AttrDict()
        self.store = AttrDict()
        self.recordlist = AttrDict()
        
        self.dialogs = AttrDict()
        
        self.table.device = meta.Table.Get ( "device" )
        print self.table.device.subclasses
        
        self.form.device = orm.Form ( self.table.device, recordclass = rDevice  )                
        self.devicerecord.enableChildren()                
        
        
        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow (self)

    def getCurrentDeviceRecord(self):
        return self.form.device.current
    
    devicerecord = property(getCurrentDeviceRecord)