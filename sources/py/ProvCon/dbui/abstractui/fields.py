from ProvCon.dbui.orm import RecordList
from ProvCon.func.variables import TracedVariable as tVar

class BaseFieldEditor(object):
    def __init__(self, field, *args, **kwargs):        
        self.variable = kwargs["variable"]  
        self.field = field
        self.vtrace = self.variable.trace ( 'w', self.variable_changed )
        
    def variable_changed(self, action, value, *args):        
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
        self.array = []   
        self.size = -1

    def resize_editor(self, newsize):
        raise NotImplementedError()
    
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

    def update_variable(self):
        try:
            self.vtrace.freeze()
            self.variable[self.idx] =  self.get_current_editor_value() 
        finally:
            self.vtrace.thaw()        
    