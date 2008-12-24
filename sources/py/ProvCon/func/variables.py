#$Id$
import exceptions

__revision__ = "$Revision$"

from decorators import singleentry, singleentryfallback

class VariableError(exceptions.BaseException):
    pass

class VariableCancel(VariableError):
    pass

class TracedVariable(object):    
    """TracedVariables are simple pythonic values which support tracing all changes in their values
    via callback functions. The API resembles that of traced variables used in Tcl/Tk.
    To define a variable you have to create a TracedVariable object:
    >> v = TracedVariable ( [name=varname:string]  )
    to set or retrieve the current variable value use:
    >> x = v.get()
    >> v.set (x)
    Traced variables may hold arrays:
    >> v[0] = 'xxx'
    >> x = v[1]
    To register a callback use the 'trace' method:
    >> tracer_obj = v.trace ( mode, callback )
    Where mode is 'r', 'w' or 'rw' and callback is the callback function with this signature:
        def _callback ( action, value, variable, index )
        where: 
         action is 'r' or 'w' depending on the action that caused the callback to be fired,
         value is the new value of the variable
         variable is the variable :)
         index is the index of the item changed if the variable holds an array. If index is None
           then either the variable is not an array or the entire value was changed (not just one
           item).
    v.trace returns a Tracer object, which is a callable wrapper for the callback function  
    supporting 'freeze' and 'thaw' methods, and may be unregistered with a call to the 'untrace'
    method.
    
    A callback function may raise VariableCancel which stops processing the current event, and
    when the current operation is a write, resets the value. (NOT YET IMPLEMENTED)
    >> tracer_obj.untrace()    
    """
    class Tracer:
        """A wrapped callback function for traced variables"""
        W = 'w'
        R = 'r'
        RW = 'rw'
        
        def __init__(self, variable, mode, callback, name = ""):
            self.variable = variable
            self.mode = mode            
            self.name = name    #naming callbacks simplifies debugging
            self.callback = callback
            self.variable._append_tracer (self)
            self.frozen = False
            
        def __repr__(self):
            return "<Tracer '" + self.mode + "' of " + str(self.variable) + " '" + self.name + "' (%x)>" % id(self)

        def untrace (self):
            self.variable.untrace (self)
        
        def __del__(self):            
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
        
        #tracers registered while a write operation is in progress, are queued in pending_tracers
        #and activated after the write operation is done
        self.pending_tracers = []

        self.frozen_callbacks = False
        self.value = None
        
        self.name = "TracedVariable(" + str(kkw.get("name", hash(self))) + ")"

    def _append_tracer(self, tracer, ignore_reentry=False):
        """Register a tracer object. Do NOT call directly, is called by Tracer.__init__"""
        if not ignore_reentry and (self.set.entered or self.__setitem__.entered):
            self.pending_tracers.append (tracer)
            return
        for m in tracer.mode:
            try:
                self.tracers[m].add ( tracer )
            except KeyError:
                raise VariableError ( "Invalid tracing mode: '%s'" % m )    
    
    def get(self):
        """Get current value"""
        for t in self.tracers['r']: t( 'r', self.value, self )
        return self.value

    def __setitem__(self, itemidx, itemvalue):
        """Set subitem value"""
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
        """Set value"""
        try:
            self.value = value
            if not self.frozen_callbacks:
                for t in self.tracers['w']: t( 'w', value, self )            
            ##Add tracers added while current tracers were iterated
            for t in self.pending_tracers: self._append_tracer(t, True)
            self.pending_tracers = []
        except VariableCancel:
            pass
        
    
    def trace(self, mode, callback, **kkw):
        """Create, register and return a new tracer object"""
        return TracedVariable.Tracer ( self, mode, callback, **kkw )
    
    def untrace(self, tracer):
        """Unregister the tracer object. Do NOT call directly, gets called by Tracer.untrace"""
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
    