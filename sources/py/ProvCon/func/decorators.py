import exceptions

class ReentryError(exceptions.BaseException):
    pass

def singleentry(raise_exception=True, default_value=None):
    """
    Raise an exception if the decorated function is called recursively
    """
    class _callable:
        def __init__(self, fn):
            self.entered = False
            self.fn = fn
            self.__repr__ = lambda self=self: "<singlentry " + str(fn) + ">"            
            
        def __call__(self, *args, **kwargs):            
            if not self.entered:
                try:
                    self.entered = True
                    return self.fn(*args, **kwargs)
                finally:
                    self.entered = False
            else:
                if raise_exception:                    
                    raise ReentryError ( str(self) )
                else:
                    return default_value
                
    return _callable

                
def singleentryfallback(fallback):
    """
    Call 'fallback' instead of the decorated function if the fn is called
    recursively
    """
    class _callable:
        def __init__(self, fn):
            self.entered = False
            self.__repr__ = lambda self=self: "<singlentry " + fn.__name__ + " fallback: " + fallback.__name__ + ">"
            self.fn = fn
            
        def __call__(self):
            if not self.entered:
                try:
                    self.entered = True
                    return self.fn(*args, **kwargs)
                finally:
                    self.entered = False
            else:
                return fallback (*args, **kwargs)
    return _callable

            