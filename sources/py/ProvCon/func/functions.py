
def partial (func, *args, **kwargs):
    def __fobj(*cargs, **kwcargs):
        call_args = args + cargs
        kwcargs.update (kwargs)        
        return func(*call_args, **kwcargs)
    #__fobj.__name__ = "partial " + func.__name__ + "(" + ",".join(map (str, args)) + ")"
    #__fobj.____ = "Partially applied " + func.__name__ + "\n" + func.__doc__
    return __fobj