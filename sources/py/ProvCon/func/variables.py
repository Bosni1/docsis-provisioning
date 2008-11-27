import exceptions

from decorators import singleentry, singleentryfallback

class VariableError(exceptions.BaseException):
    pass

class VariableCancel(VariableError):
    pass

class TracedVariable(object):    
    class Tracer:
        W = 'w'
        R = 'r'
        RW = 'rw'
        
        def __init__(self, variable, mode, callback, name = ""):
            self.variable = variable
            self.mode = mode
            self.name = name
            self.callback = callback
            self.variable._append_tracer (self)
            self.frozen = False
            
        def __repr__(self):
            return "<Tracer '" + self.mode + "' of " + str(self.variable) + " '" + self.name + "' (%x)>" % id(self)

        def __del__(self):
            print "del", self
            self.variable.untrace (self)
            
        def __call__(self, action, value, var=None, idx=None):
            if not self.frozen:
                #print "Calling: " + str(self)
                return self.callback ( action, value, var, idx )
        
        def freeze(self): self.frozen = True
        def thaw(self): self.frozen = False
            
            
    def __init__(self, **kkw):
        self.tracers = { 'r' : set(), 'w' : set() }        
        self.set = singleentry ( False ) ( self.set )
        self.__setitem__ = singleentry ( False ) ( self.__setitem__ )
        self.pending_tracers = []
        self.frozen_callbacks = False
        self.value = None
        
        self.name = "TracedVariable(" + str(kkw.get("name", hash(self))) + ")"

    def _append_tracer(self, tracer, ignore_reentry=False):
        if not ignore_reentry and (self.set.entered or self.__setitem__.entered):
            self.pending_tracers.append (tracer)
            return
        for m in tracer.mode:
            try:
                self.tracers[m].add ( tracer )
            except KeyError:
                raise VariableError ( "Invalid tracing mode: '%s'" % m )    
    
    def get(self):
        for t in self.tracers['r']: t( 'r', self.value, self )
        return self.value

    def __setitem__(self, itemidx, itemvalue):
        if not (isinstance(self.value, (list, tuple, dict))):
            return                
        try:
            item = self.value[itemidx]
            if not self.frozen_callbacks:
                for t in self.tracers['w']: t( 'w', itemvalue, self, itemidx )
            self.value[itemidx] = itemvalue
            ##Add tracers added while current tracers were iterated
            for t in self.pending_tracers: self._append_tracer(t, True)
            self.pending_tracers = []
        except KeyError:
            return

    def __getitem__(self, itemidx, itemvalue):
        if not (isinstance(self.value, (list, tuple, dict))):
            return None
        
        try:
            return self.value[itemidx]
        except KeyError:
            return None
        
    def set(self, value):
        try:
            if not self.frozen_callbacks:
                for t in self.tracers['w']: t( 'w', value, self )
            self.value = value
            ##Add tracers added while current tracers were iterated
            for t in self.pending_tracers: self._append_tracer(t, True)
            self.pending_tracers = []
        except VariableCancel:
            pass
        
    
    def trace(self, mode, callback, **kkw):
        return TracedVariable.Tracer ( self, mode, callback, **kkw )
    
    def untrace(self, tracer):
        for m in self.tracers: 
            try: 
                self.tracers[m].remove(tracer)
            except KeyError:
                pass

    trace_vdelete = untrace
    
    def info(self):
        return self.tracers
    
    trace_vinfo = info
    
    def freeze(self): self.frozen_callbacks = True
    def thaw(self): self.frozen_callbacks = False
    
    def __repr__(self):
        return self.name
    