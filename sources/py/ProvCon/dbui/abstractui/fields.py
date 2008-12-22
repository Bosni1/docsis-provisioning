"""
=== Base classes for field-editing widgets ===

These are the basic types of field-editing widgets:

* simple editors : editors that hold one, easily editable value
* reference editors : used for editing fields which reference other records
* array editors : editing fields that hold arrays

Array editors, are a container for a number of simple/reference editors, they
act as a proxy for unpacking the array into simple values, and then packing them
back into their traced variable.

"""
from ProvCon.dbui.orm import RecordList
from ProvCon.func.variables import TracedVariable as tVar

class BaseFieldEditor(object):
    """Base class for all editor widgets"""
    def __init__(self, field, *args, **kwargs):        
        self.__variable = None   #holder for the 'variable' property
        self.__vtrace  = None    #holder for the 'vtrace' property
        self.field = field
        self.variable = kwargs["variable"]  
                
    def _get_variable(self):
        return self.__variable    
    def _set_variable(self, tvar):
        #When the traced variable changes, try to be nice and remove our tracer
        if self.__vtrace:
            self.__vtrace.untrace()
        self.__variable = tvar
        self.__vtrace = self.variable.trace ( 'w', self.variable_changed, name=str(self) )
    variable = property (_get_variable, _set_variable )

    def _get_vtrace(self): return self.__vtrace
    vtrace = property(_get_vtrace)
    
    def variable_changed(self, action, value, var=None, idx=None, *args):
        """Callback function that handles variable value changes."""
        self.set_current_editor_value(value)
            
    def update_variable(self):
        """Function used to update traced variable to the currently edited value.
        For example - TextBox widget's 'text' property will only be sent back to the
        traced variable when this function is called"""
        try:
            #freeze the callback to avoid infinite recursion
            self.vtrace.freeze()            
            self.variable.set ( self.get_current_editor_value() )
        finally:
            self.vtrace.thaw()        

    def set_current_editor_value(self, value):
        """This function is responsible for setting the currently edited value to the traced
        variable's value. (For example, when a record is reloaded or changed) A subclass 
        implementation will propagate variable's value to the underlying widget (eg. by setting
        TextBox's 'text' property'.
        This function is called by the variable's trace function and should not be called directly.
        """
        raise NotImplementedError()
    
    def get_current_editor_value(self):
        """This function must return the value currently held by the editor (like TextBox's 'text'
        property). It is called by the update_variable function to set the traced variable's value.
        Using this function should be considered unrecommended, since it will usually access gui-toolkit
        specific details. Use editor.variable.get() instead."""
        return self.variable.get()
    
    def __repr__(self):
        return "<Editor " + self.field.name  + ">"
    
class BaseReferenceEditor(BaseFieldEditor):
    """BaseReferenceEditor
    Base class for editors of fields which reference other records. 
    A reference field, by assumption, holds the 'objectid' of the record it references.
    Since reference editors are usually widgets similar to combo boxes, the base reference editor
    may retrieve a list of records from the referenced table, if the 'getrecords' keyword variable
    is passed to the constructor.
    """
    def __init__(self, field, getrecords=True, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, *args, **kwargs)
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        if getrecords:
            self.records = RecordList ( self.field.reference )
            self.records.reload()
        else:
            self.records = None
            
class BaseArrayEditor(BaseFieldEditor):
    """BaseArrayEditor
    A base class for widgets used to edit arrays.

    Concrete implementations should not subclass this class, but rather use the
    ConcreteBaseArrayEditor as their parent.    
    """
    def __init__(self, field, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, *args, **kwargs)
        self.recordlist = kwargs.get ( "recordlist", None )
        self.choices = kwargs.get ( "choices", [] )
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        self.array = []   
        self.size = -1

    def variable_changed(self, action, value, var=None, idx=None, *args):        
        """Traced variables support indexed assignment and retrieval. When a variable changes
        due to a change in one of its subitems the callback is passed the subitem's index, otherwise
        the index is None. When the index is None, it means that the entire value changed, so we call
        set_current_editor_value to update the widget."""        
        if idx is None:
            self.set_current_editor_value(value)

    def resize_editor(self, newsize):
        """This function gets called when the number of edited elements changes, and it must
        be reflected by the editor widget."""
        raise NotImplementedError()    

    def insert_item(self, atidx, itemvalue=None):
        array = self.variable.get()        
        if array is None:
            array = [itemvalue]
        else:
            array.insert (atidx, itemvalue)
        self.variable.set ( array )

    def remove_item(self, atidx):
        array = self.variable.get()
        del array[atidx]        
        self.variable.set ( array )

    def swap_items(self, idx1, idx2):
        array = self.variable.get()
        a1 = array[idx1]
        a2 = array[idx2]
        self.variable[idx1] = a2
        self.variable[idx2] = a1
                
    def set_current_editor_value(self, value):         
        self.array = value
        if value is None:
            self.resize_editor(0)
        else:
            self.resize_editor ( len (self.array) )        
            for idx, item in enumerate(self.array):
                if idx < self.size:
                    self.set_current_editor_item_value (idx, item)
            
    def set_current_editor_item_value(self, idx, value):
        raise NotImplementedError()
    
    def get_current_editor_value(self):
        raise NotImplementedError()
    
    def get_current_editor_item_value(self, idx):
        raise NotImplementedError()

def ConcreteBaseArrayEditor(ItemEditorClass, ButtonBoxClass):
    class ConcreteArrayEditor(BaseArrayEditor):        
        @staticmethod
        def get_item_editor_class(): return ItemEditorClass
        @staticmethod
        def get_button_box_class(): return ButtonBoxClass
    return ConcreteArrayEditor
    
class BaseArrayItemEditor(BaseFieldEditor):
    def __init__(self, field, parenteditor, idx, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, variable=parenteditor.variable, **kwargs)                
        self.parenteditor = parenteditor
        self.idx = idx
        
    def variable_changed(self, action, value, var, idx, *args):        
        if idx == self.idx:
            self.set_current_editor_value(value)
            
    def initialize_value(self, value):
        """called by the ArrayEditor when a new record/value is loaded"""
        raise NotImplementedError
            
    def update_variable(self):
        try:
            self.vtrace.freeze()
            self.variable[self.idx] =  self.get_current_editor_value() 
        finally:
            self.vtrace.thaw()        
                
    def __repr__(self):
        return "<ItemEditor " + self.field.name + "[" + str(self.idx) + "]>"
    
class BaseArrayItemButtonBox(object):
    def __init__(self, arrayeditor, idx, **kkw):
        self.arrayeditor = arrayeditor
        self.idx = idx
        self.commands = filter ( lambda k: kkw[k], kkw )
        
    def command_insert(self, *args):        
        self.arrayeditor.insert_item (self.idx+1, None)
        
    def command_delete(self, *args):
        self.arrayeditor.remove_item (self.idx)
        
        