from ProvCon.dbui.orm import RecordList

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
    def __init__(self, field, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, *args, **kwargs)
        self.array = []
    
    def resize_editor (self, newsize):
        raise NotImplementedError()
    
    def set_current_editor_value(self, value):
        self.array = value
        self.resize_editor ( len (self.array) )
        for idx, item in enumerate(self.array): 
            self.set_current_editor_item_value (idx, item)
            
    def set_current_editor_item_value(self, idx, value):
        raise NotImplementedError()
    
    def get_current_editor_value(self):
        raise NotImplementedError()
    
    def get_current_editor_item_value(self, idx):
        raise NotImplementedError()

class BaseArrayItem(BaseFieldEditor):
    def __init__(self, field, idx, *args, **kwargs):
        BaseFieldEditor.__init__ (self, field, *args, **kwargs)                
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
    