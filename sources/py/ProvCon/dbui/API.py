

def Implements(*interfaces):
    def DoCheck(cls):
        print "Checking the implementation of " + str(map(lambda i: i.__name__, interfaces)) + " in " + str(cls.__name__)
        for i in interfaces:
            for method in dir(i):
                if method.startswith ("__") and method.endswith("__"): continue
                iattr = getattr(i, method)                
                try:
                    cattr = getattr(cls, method)
                except AttributeError:
                    if isinstance(iattr, property):
                        attrtype = 'property'
                    else:
                        attrtype = 'method'
                    print " + Warning! Incomplete implementation of '" + i.__name__ + "' in '" + cls.__name__ + "' " + attrtype + "  '" + method + "' is missing."               
                    continue
              
        return cls
    return DoCheck
    
class Interface: 
    __emits__ = []

class IRecordList(Interface):
    """
    iterable
    """
    def reload(): pass
    def reloadsingle(objectid): pass
    def clear(): pass
    def getindex(objectid): pass
    def getbyid(objectid): pass

class IRecordListHolder(Interface):    
    def set_records(recordlist): pass
    def get_records(): pass
    records = property()    

class IDumbNavigator(Interface):
    """
    EMITS: navigate
    """

class IRecordHolder(Interface):
    """
    EMITS: request_record_change
    EMITS: current_record_changed
    EMITS: navigate
    EMITS: data_loaded    
    """
    current = property()
    def setid(id): pass
    def revert(): pass    

class INavigator(IDumbNavigator, IRecordListHolder):    
    def navigate(recordindex): pass
    def first(): pass
    def prev(): pass
    def next(): pass
    def last(): pass
    def currentid(): pass
    def currentrecord(): pass
    def indexof(id): pass


class IRecordController(IRecordHolder):
    """
    EMITS: current_record_modified
    EMITS: current_record_saved
    EMITS: current_record_deleted    
    """
    def save(): pass    
    def delete(): pass
    def getvar(fieldname): pass

class IForm(IRecordController):
    """
    EMITS: new_record
    """
    def new(): pass

    
    
    
    
    
        
    
        
