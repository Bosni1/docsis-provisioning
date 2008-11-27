##!/bin/env python
## -*- coding: utf8 -*-
#from orm import *
#from ProvCon.func.variables import TracedVariable as StringVar
#from gettext import gettext as _
#from ProvCon.func import *

#class Form(eventemitter):
    #""" ==class Form==
    #Forms play a role similar to the one controllers play in the MVC model.
    #They serve as an interface between Record objects (the model), and 
    #GUI editors (the view).
    #Forms hold Table objects.
    #The heart of a Form is a list of TkVariables, which are used by the GUI
    #as data storage of the editor widgets. Forms trace all changes to the variables
    #and propagate them to the Record objects.
    
    #instance variables worth mentioning:
    #Form.table   ->  reference to a Table object
    #Form.current ->  currently edited Record
    #Form.tkvars  ->  a field name-indexed hash of tk variables
    
    #methods:
    #save, reload, delete, new  ->   database operations on the current record
    #setid (objectid)  ->  load a row identified by objectid into the current record
    
    #Forms are also eventemmiters.
    #events:
    #before_current_record_change - event handler may cancel record change
    #current_record_changed
    #new_record
    #data_loaded
    #"""
    #def __init__(self, table, **kkw):
        #eventemitter.__init__(self,                               
                              #[ "request_record_change",
                                #"current_record_changed",
                                #"current_record_modified",
                                #"current_record_deleted",
                                #"current_record_saved",
                                #"navigate",
                                #"new_record", 
                                #"data_loaded" ] 
                              #)
        #self.on_record_changed_handler = conditionalmethod (self.on_record_changed_handler)
        #self.value_change_handler = conditionalmethod (self.value_change_handler)
        #self.on_edit_handler = conditionalmethod(self.on_edit_handler)

        #self.variableclass = kkw.get ( "variableclass" , StringVar )
        
        #self.table = table
        #self.current = Record.EMPTY (table.name)
        #self.tkvars = {}
        #self.modification_notification = False
        
        #for f in self.table:
            #self.tkvars[f.name] = self.variableclass( name=self.table.name + "." + f.name)
            #self.tkvars[f.name].trace ( 'w', partial (self.value_change_handler, f.name), name="form of " + self.table.name ) 
        
    #def __getitem__(self, itemidx):
        #return self.tkvars[itemidx]
    
    #def save(self):
        #wasnew = self.current._isnew
        #self.current.write()        
        #self.on_record_changed_handler()
        #self.emit_event ( "current_record_saved", self.current, wasnew )
        #self.modification_notification = False

    #def reload(self):
        #self.current.read()
        #self.on_record_changed_handler()        
        #self.emit_event ( "data_loaded", self.current )
        #self.emit_event ( "navigate", self.current.objectid )
        #self.modification_notification = False

    #def new(self):        
        #self.current.setObjectID ( None )
        #self.on_record_changed_handler()
        #self.emit_event ( "new_record", self.current )
        #self.emit_event ( "navigate", None )

    #def setid(self, objectid):
        #"""this function is used by the GUI to load a record into a form"""
        ###TODO: it would be much prettier if this was done with events:
        ###   1. this function calls setObjectID on the current record
        ###   2. the record emits a 'record_changed' event
        ###   3. form's handler of this event fills in the values
        #if self.emit_event ( "request_record_change", self.current, objectid ) is not None:
            #return False
        #self.current.setObjectID ( objectid )
        #self.on_record_changed_handler()
        #self.emit_event ( "current_record_changed", self.current )
        #self.emit_event ( "navigate", self.current.objectid )
        
    #def delete(self):
        #objid = self.current.objectid
        #self.current.delete()
        #self.emit_event ( "current_record_deleted", objid )

    #def on_edit_handler (self, fieldname):        
        #"""The tkVariable was changed, propagate this value to the current record"""
        #self.current.setFieldStringValue ( fieldname, self.tkvars[fieldname].get() )
        #if self.current._ismodified and not self.modification_notification:
            #self.modification_notification = True
            #self.emit_event ( "current_record_modified", self.current )
            
    #def value_change_handler(self, fname, *args):                        
        #"""The tkVariable was changed, propagate this value to the handler
        #This is invoked when the set method on one of the form's tkvars is called
        #"""
        #try:
            #self.value_change_handler.freeze()
            #if fname in self.table: self.on_edit_handler ( fname )
        #finally:
            #self.value_change_handler.thaw()
                    
    #def on_record_changed_handler(self):
        #"""The current record was changed, so fill the tkVariables with the record values"""
        #try:
            ##We will be changing the tkvars so freeze their handler for now
            #self.value_change_handler.freeze()
            #for f in self.table:
                #self.tkvars[f.name].set ( self.current.getFieldValue ( f.name ) )
        #finally:
            #self.value_change_handler.thaw()
    
#def BaseSpecializedForm(table):
    #class _Form(Form):
        #def __init__(self):
            #Form.__init__(self, table)
    #return _Form        
    
#class Navigator(eventemitter):
    #def __init__(self):
        #eventemitter.__init__ (self, [
            #"navigate" ,
        #])
                               
        #self.records = []
        #self.currentidx = 0
        
    #def navigate (self, relative):
        #return self.navigateabsolute (self.currentidx + relative )        
    
    #def navigateabsolute (self, idx):
        #if len(self) == 0: return None
        #if idx > len(self): idx = idx - len(self)
        #if idx <= 0: idx = len(self) + idx
        #self.currentidx = idx
        #self.emit_event ( "navigate", idx, self.records[idx] )        
        #return self.current()
    
    #def setrecords (self, rl):
        #self.records = rl
        #if len(rl) > 0: self.navigateabsolute(1)
        
    #def current(self):
        #return self.records[self.currentidx - 1]
    
    #def currentid(self):
        #return self.current()['objectid']
    
    #def __len__(self):
        #return len(self.records)

    #def next(self):
        #return self.navigate(1)
    
    #def prev(self):
        #return self.navigate(-1)
    
    #def first(self):
        #return self.navigateabsolute(1)

    #def last(self):
        #return self.navigateabsolute( len(self) )

#class RecordPager(object):
    #def __init__(self, *args, **kwargs):
        ##kwargs: query, table, pagesize, idlist
        #self.records = []
        #self.records_hash = {}
        #self.total_record_count = -1
        #self.current_page = -1
        
    #def getrecordbyid(self, objectid): return self.records_hash[objectid]
    #def setobjectids(self, objids): pass
    #def setrecords(self, records): pass
    #def setpage(self, idx): pass
    #def moverel(self, moveby): pass
    #def next(self): pass
    #def prev(self): pass
    #def first(self): pass
    #def last(self): pass
    #def refresh(self): pass
    #def __iter__(self): pass    


        
