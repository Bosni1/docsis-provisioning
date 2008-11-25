import exceptions

def partial (func, *args, **kwargs):
    def __fobj(*cargs, **kwcargs):
        call_args = args + cargs
        kwcargs.update (kwargs)        
        return func(*call_args, **kwcargs)
    #__fobj.__name__ = "partial " + func.__name__ + "(" + ",".join(map (str, args)) + ")"
    #__fobj.____ = "Partially applied " + func.__name__ + "\n" + func.__doc__
    return __fobj

def find_method_for_superclass(obj, prefix, record, default):
    table = record._table
    while table is not None:
        try:
            return getattr(obj, prefix + "_" + table.name)
        except AttributeError:
            table = table.superclass
    return default


class conditionalmethod:
    def __init__(self, method):
        self.frozen = False
        self.method = method               
    def __call__(self, *args, **kwargs):        
        if self.frozen: return None        
        return self.method ( *args, **kwargs )
    def freeze (self):
        self.frozen = True        
    def thaw(self):
        self.frozen = False

class eventexception(exceptions.Exception):
    def __init__(self, retval):
        exceptions.Exception.__init__ (self)
        self.ret = retval    

class eventcancelled(eventexception):
    pass

class eventemitter(object):
    class evthook(object):
        def __init__(self, num, evt, cb):
            self.num = num
            self.evt = evt
            self.cb = cb
            self.frozen = False
            
        def __call__(self, *args, **kwargs):
            if not self.frozen:
                return self.cb ( *args, **kwargs )
        
        def freeze(self): self.frozen = True
        def thaw(self): self.frozen = False
        def remove(self): self.evt.remove (self)
        
    class evt(list):
        def __init__(self, emitter):
            self.emitter = emitter
            self.frozen = False
            
        def listen(self, callback):
            num = len(self)
            self.append (eventemitter.evthook (num, self, callback))
            return self[-1]
        
        def emit(self, *args, **kwargs):
            try:
                if not self.frozen:
                    for h in self: h(*args, **kwargs)
            except eventexception, e:
                return e.ret
            return None
        
        def freeze(self): self.frozen = True
        def thaw(self): self.frozen = False
    
    def __init__(self, events=[]):
        self.__myevents = {}
        for i in events: self.__myevents[i] = self.evt(self)
    
    def register_event_hook (self, evtname, cb):
        return self.__myevents[evtname].listen (cb)
    
    def emit_event (self, evtname, *args, **kwargs):
        self.__myevents[evtname].emit(*args, **kwargs)
        