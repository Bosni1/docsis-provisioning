import exceptions

class eventexception(exceptions.Exception):
    def __init__(self, retval=None):
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
            if not self.frozen:
                for h in self: h(*args, **kwargs)
        
        def freeze(self): self.frozen = True
        def thaw(self): self.frozen = False
    
    def __init__(self, events=[]):
        self.__myevents = {}
        for i in events: self.add_emitted_event ( i )

    def add_emitted_event (self, eventname):
        self.__myevents[eventname] = self.evt(self)
        
    def register_event_hook (self, evtname, cb):
        return self.__myevents[evtname].listen (cb)
    
    def emit_event (self, evtname, *args, **kwargs):
        self.__myevents[evtname].emit(*args, **kwargs)
        
        