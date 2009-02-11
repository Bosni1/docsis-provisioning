#!/bin/env python
# -*- coding: utf8 -*-
##$Id$

from ProvCon.func.variables import TracedVariable as StringVar
from ProvCon.dbui.API import Implements, IForm
from gettext import gettext as _
from ProvCon.func import *

__revision__ = "$Revision$"

@Implements(IForm)
class Form(eventemitter):
    """ ==class Form==

    Implemented interfaces: IForm
    
    Forms play a role similar to the one controllers play in the MVC model.
    They serve as an interface between Record objects (the model), and 
    GUI editors (the view).
    Each Form holds a reference to a Table object.
    
    The heart of a Form is a list of TkVariables, which are used by the GUI
    as data storage of the editor widgets. Forms trace all changes to the variables
    and propagate them to the Record objects.
    
    As far as Forms are concerned the Record objects are dumb. The Form does not register
    any handlers for Record's events, therefore all changes to the "current" record made
    directly to the Record (not through the traced variable interface), may be lost.
    
    instance variables worth mentioning:
    Form.table   ->  reference to a Table object
    Form.current ->  currently edited Record
    Form.tkvars  ->  a field name-indexed hash of tk variables
    
    methods:
    save, reload, delete, new  ->   database operations on the current record
    setid (objectid)  ->  load a row identified by objectid into the current record
    
    Events raised by form objects:
    before_current_record_change - raised when a request to change the current record
    
    current_record_changed
    new_record
    data_loaded
    """
    def __init__(self, table, **kkw):
        eventemitter.__init__(self,                               
                              [ "request_record_change",
                                "current_record_changed",
                                "current_record_modified",
                                "current_record_deleted",
                                "current_record_saved",
                                "navigate",
                                "new_record", 
                                "data_loaded" ] 
                              )
        self.on_record_changed_handler = conditionalmethod (self.on_record_changed_handler)
        self.value_change_handler = conditionalmethod (self.value_change_handler)
        self.on_edit_handler = conditionalmethod(self.on_edit_handler)

        self.variableclass = kkw.get ( "variableclass" , StringVar )
        
        from record import Record
        from record import ORMError 
        from ProvCon.dbui.database import RaiseDBException

        self.ormerror = ORMError
        self.ormerrorhandler = RaiseDBException
        self.table = table
        self.current = Record.EMPTY (table.name)
        self.tkvars = {}
        self.modification_notification = False
        
        for f in self.table:
            self.tkvars[f.name] = self.variableclass( name=self.table.name + "." + f.name)
            self.tkvars[f.name].trace ( 'w', partial (self.value_change_handler, f.name), name="form of " + self.table.name ) 

        self.extra_fields = kkw.get ( "extra_fields", [] )
        self.extra_fields_hash = {}
        for f in self.extra_fields:
            self.extra_fields_hash[f.name] = f
            self.tkvars[f.name] = self.variableclass( name=self.table.name + "." + f.name)
            self.tkvars[f.name].trace ( 'w', partial (self.value_change_handler, f.name), name="form of " + self.table.name ) 
                    
        self.defaultvalues = kkw.get ( "defaults", {} )
        self.fixed_fields = kkw.get ( "fixed_fields", {} )
        
    def get_current_record(self):
        return self.__current    
    def set_current_record(self, r):
        self.__current = r
    current = property(get_current_record, set_current_record)

    def is_field_fixed(self, fieldname):
        return fieldname in self.fixed_fields
    
    def get_fixed_value(self, fieldname):
        try:
            return self.fixed_fields[fieldname]
        except KeyError:
            return None

    def set_fixed_value(self, fieldname, fieldvalue):
        self.fixed_fields[fieldname] = fieldvalue
        
    def del_fixed_value(self, fieldname):
        try:
            del self.fixed_fields[fieldname]
        except KeyError:
            pass

    def set_all_fixed_fields(self):
        for fname in self.fixed_fields:
            self.current[fname] = self.fixed_fields[fname]
            
    def getvar(self, fieldname):
        return self.tkvars[fieldname]
    
    def save(self):
        try:
            wasnew = self.current._isnew
            for extra_field in self.extra_fields: extra_field.pre_write ( self )
            self.current.write()        
            for extra_field in self.extra_fields: extra_field.post_write ( self )
            self.on_record_changed_handler()
            self.raiseEvent ( "current_record_saved", self.current, wasnew )
            self.modification_notification = False
        except self.ormerror, e:
            self.ormerrorhandler (e)

    def revert(self):
        try:
            for extra_field in self.extra_fields: extra_field.pre_read ( self )
            self.current.read()
            self.set_all_fixed_fields()
            for extra_field in self.extra_fields: extra_field.post_read ( self )
            self.on_record_changed_handler()        
            self.raiseEvent ( "data_loaded", self.current )
            self.raiseEvent ( "navigate", self.current.objectid )
            self.modification_notification = False
        except self.ormerror, e:
            self.ormerrorhandler(e)

    def new(self):        
        try:
            self.raiseEvent ( "request_record_change", self.current, None )
        except eventcancelled:
            return False
        
        for extra_field in self.extra_fields: extra_field.new ( self )
        self.current.setObjectID ( None )
        self.set_all_fixed_fields()
        
        for fname in self.defaultvalues:
            self.current[fname] = self.defaultvalues[fname]            
            if self.is_field_fixed(fname): self.current[fname] = self.get_fixed_value(fname)
            
        self.on_record_changed_handler()
        self.raiseEvent ( "new_record", self.current )
        self.raiseEvent ( "current_record_changed", self.current )
        self.raiseEvent ( "navigate", None )

    def setid(self, objectid):
        """this function is used by the GUI to load a record into a form"""
        ##TODO: it would be much prettier if this was done with events:
        ##   1. this function calls setObjectID on the current record
        ##   2. the record emits a 'record_changed' event
        ##   3. form's handler of this event fills in the values
        try:
            self.raiseEvent ( "request_record_change", self.current, objectid )
        except eventcancelled:
            return False
        try:
            for extra_field in self.extra_fields: extra_field.pre_read ( self )                        
            self.current.setObjectID ( objectid )
            self.set_all_fixed_fields()
            for extra_field in self.extra_fields: extra_field.post_read ( self )
            self.on_record_changed_handler()
            self.modification_notification = False
            self.raiseEvent ( "data_loaded", self.current )
            self.raiseEvent ( "current_record_changed", self.current )
            self.raiseEvent ( "navigate", self.current.objectid )        
        except self.ormerror, e:
            self.ormerrorhandler (e)
            
    def delete(self):
        try:
            objid = self.current.objectid
            for extra_field in self.extra_fields: extra_field.pre_delete ( self )                        
            self.current.delete()
            for extra_field in self.extra_fields: extra_field.post_delete ( self )                        
            self.raiseEvent ( "current_record_deleted", objid )
        except self.ormerror, e:
            self.ormerrorhandler(e)

    def on_edit_handler (self, fieldname):        
        """The tkVariable was changed, propagate this value to the current record"""        
        self.current.setFieldValue ( fieldname, self.tkvars[fieldname].get() )
        if self.current._ismodified and not self.modification_notification:
            self.modification_notification = True
            self.raiseEvent ( "current_record_modified", self.current )
            
    def value_change_handler(self, fname, *args):                        
        """The tkVariable was changed, propagate this value to the handler
        This is invoked when the set method on one of the form's tkvars is called
        """
        try:
            self.value_change_handler.freeze()
            if fname in self.table: self.on_edit_handler ( fname )
            elif fname in self.extra_fields_hash: self.extra_fields_hash[fname].value_changed ( self )
        finally:
            self.value_change_handler.thaw()
                    
    def on_record_changed_handler(self):
        """The current record was changed, so fill the tkVariables with the record values"""
        try:
            #We will be changing the tkvars so freeze their handler for now
            self.value_change_handler.freeze()
            for f in self.table:
                self.tkvars[f.name].set ( self.current.getFieldValue ( f.name ) )
            for f in self.extra_fields:
                f.init_value (self)
        finally:
            self.value_change_handler.thaw()
    
def BaseSpecializedForm(table):
    class _Form(Form):
        def __init__(self):
            Form.__init__(self, table)
    return _Form        
    
  


        
