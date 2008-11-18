#!/bin/env python
# -*- coding: utf8 -*-
from orm import *
import Tix
from Tkconstants import *
import tkCommonDialog
import tkMessageBox, traceback
from gettext import gettext as _
from misc import *

class Form(eventemitter):
    """ ==class Form==
    Forms play a role similar to the one controllers play in the MVC model.
    They serve as an interface between Record objects (the model), and 
    GUI editors (the view).
    Forms hold Table objects.
    The heart of a Form is a list of TkVariables, which are used by the GUI
    as data storage of the editor widgets. Forms trace all changes to the variables
    and propagate them to the Record objects.
    
    instance variables worth mentioning:
    Form.table   ->  reference to a Table object
    Form.current ->  currently edited Record
    Form.tkvars  ->  a field name-indexed hash of tk variables
    
    methods:
    save, reload, delete, new  ->   database operations on the current record
    setid (objectid)  ->  load a row identified by objectid into the current record
    
    Forms are also eventemmiters.
    events:
    before_current_record_change - event handler may cancel record change
    current_record_changed
    new_record
    data_loaded
    """
    def __init__(self, table):
        eventemitter.__init__(self,                               
                              [ "before_current_record_change",
                                "current_record_changed",
                                "current_record_modified",
                                "current_record_deleted",
                                "current_record_saved",
                                "new_record", 
                                "data_loaded" ] 
                              )
        self.on_record_changed_handler = conditionalmethod (self.on_record_changed_handler)
        self.value_change_handler = conditionalmethod (self.value_change_handler)
        self.on_edit_handler = conditionalmethod(self.on_edit_handler)
        
        self.table = table
        self.current = Record.EMPTY (table.name)
        self.tkvars = {}
        self.modification_notification = False
        
        for f in self.table:
            self.tkvars[f.name] = Tix.StringVar()
            self.tkvars[f.name].trace ( 'w', partial (self.value_change_handler, f.name) ) 
        
    
    def save(self):
        self.current.write()        
        self.on_record_changed_handler()
        self.emit_event ( "current_record_saved", self.current )
        self.modification_notification = False

    def reload(self):
        self.current.read()
        self.on_record_changed_handler()        
        self.emit_event ( "data_loaded", self.current )
        self.modification_notification = False

    def new(self):        
        self.current.setObjectID ( None )
        self.on_record_changed_handler()
        self.emit_event ( "new_record", self.current )

    def setid(self, objectid):
        """this function is used by the GUI to load a record into a form"""
        ##TODO: it would be much prettier if this was done with events:
        ##   1. this function calls setObjectID on the current record
        ##   2. the record emits a 'record_changed' event
        ##   3. form's handler of this event fills in the values
        self.current.setObjectID ( objectid )
        self.on_record_changed_handler()
        self.emit_event ( "current_record_changed", self.current )
        
    def delete(self):
        objid = self.current.objectid
        self.current.delete()
        self.emit_event ( "current_record_deleted", objid )

    def on_edit_handler (self, fieldname):        
        """The tkVariable was changed, propagate this value to the current record"""
        self.current.setFieldStringValue ( fieldname, self.tkvars[fieldname].get() )
        if self.current._ismodified and not self.modification_notification:
            self.modification_notification = True
            self.emit_event ( "current_record_modified", self.current )
            
    def value_change_handler(self, fname, *args):                        
        """The tkVariable was changed, propagate this value to the handler"""
        try:
            self.value_change_handler.freeze()
            if fname in self.table: self.on_edit_handler ( fname )
        finally:
            self.value_change_handler.thaw()
                    
    def on_record_changed_handler(self):
        """The current record was changed, so fill the tkVariables with the record values"""
        for f in self.table:
            self.tkvars[f.name].set ( self.current.getFieldStringValue ( f.name ) )
    
def BaseSpecializedForm(table):
    class _Form(Form):
        def __init__(self):
            Form.__init__(self, table)
    return _Form        
    
class Navigator(eventemitter):
    def __init__(self):
        eventemitter.__init__ (self, [
            "navigate" ,
        ])
                               
        self.records = []
        self.currentidx = 0
        
    def navigate (self, relative):
        return self.navigateabsolute (self.currentidx + relative )        
    
    def navigateabsolute (self, idx):
        if len(self) == 0: return None
        if idx > len(self): idx = idx - len(self)
        if idx <= 0: idx = len(self) + idx
        self.currentidx = idx
        self.emit_event ( "navigate", idx, self.records[idx] )        
        return self.current()
    
    def setrecords (self, rl):
        self.records = rl
        if len(rl) > 0: self.navigateabsolute(1)
        
    def current(self):
        return self.records[self.currentidx - 1]
    
    def currentid(self):
        return self.current()['objectid']
    
    def __len__(self):
        return len(self.records)

    def next(self):
        return self.navigate(1)
    
    def prev(self):
        return self.navigate(-1)
    
    def first(self):
        return self.navigateabsolute(1)

    def last(self):
        return self.navigateabsolute( len(self) )
    

class NavigatorWidget (Tix.Frame, Navigator):
    def __init__(self, parent, form, *args, **kwargs):
        Tix.Frame.__init__(self, parent, *args, **kwargs)
        Navigator.__init__(self)
        self.__form = form        
        self.buttons = {
            "prev" : Tix.Button (self, padx=4, pady=1, width=3, text="<<", command=self.prev),
            "next" : Tix.Button (self, padx=4, pady=1, width=3, text=">>", command=self.next),
            "save" : Tix.Button (self, padx=4, pady=1, width=3, text=">>", command=self.__form.save),
        }
        self.inputvar = Tix.StringVar()
        self.entry = Tix.Entry (self, width=40, textvariable = self.inputvar )        
        for i, b in enumerate(self.buttons.values()): b.pack (side=LEFT )
        self.entry.pack (side=RIGHT, fill=X )
        self.notify = []
        
    def onrecordchange(self, idx):
        self.inputvar.set ( self.current()['txt'] )
        for n in self.notify: n()
        
