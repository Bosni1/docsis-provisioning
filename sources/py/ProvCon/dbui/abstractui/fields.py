from ProvCon.dbui.orm import RecordList
from ProvCon.func.variables import TracedVariable as tVar

class BaseFieldEditor(object):
    def __init__(self, field, *args, **kwargs):        
        self.variable = kwargs["variable"]  
        self.field = field
        self.vtrace = self.variable.trace ( 'w', self.variable_changed, name=str(self) )
        try:
            getattr(self, "set_editor_style")()
        except AttributeError:
            pass
    def variable_changed(self, action, value, var=None, idx=None, *args):        
        self.set_current_editor_value(value)
            
    def update_variable(self):
        try:
            self.vtrace.freeze()
            self.variable.set ( self.get_current_editor_value() )
        finally:
            self.vtrace.thaw()        

    def set_current_editor_value(self, value):
        raise NotImplementedError()
    
    def get_current_editor_value(self):
        raise NotImplementedError()
    
    def __repr__(self):
        return "<Editor " + self.field.name  + ">"
    
class BaseReferenceEditor(BaseFieldEditor):
    def __init__(self, field, getrecords=True, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, *args, **kwargs)
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        if getrecords:
            self.records = RecordList ( self.field.reference )
            self.records.reload()
        else:
            self.records = None
            
class BaseArrayEditor(BaseFieldEditor):
    """
    Subclasses must implement following methods:
    - resize_editor (self, newsize)
    """
    def __init__(self, field, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, *args, **kwargs)
        self.recordlist = kwargs.get ( "recordlist", None )
        self.choices = kwargs.get ( "choices", [] )
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt )
        self.array = []   
        self.size = -1

    def variable_changed(self, action, value, var=None, idx=None, *args):        
        if idx is None:
            self.set_current_editor_value(value)

    def resize_editor(self, newsize):
        raise NotImplementedError()    

    def insert_item(self, atidx, itemvalue=None):
        array = self.variable.get()        
        #print array
        array.insert (atidx, itemvalue)
        #print "Insert at ", atidx
        #print array
        #print "---"
        self.variable.set ( array )

    def remove_item(self, atidx):
        array = self.variable.get()
        #print array                
        del array[atidx]        
        #print "Removal of ", atidx
        #print array
        #print "---"

        self.variable.set ( array )

    def swap_items(self, idx1, idx2):
        array = self.variable.get()
        a1 = array[idx1]
        a2 = array[idx2]
        self.variable[idx1] = a2
        self.variable[idx2] = a1
                
    def set_current_editor_value(self, value):        
        self.array = value
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
        
        