
class conditionalmethod:
    def __init__(self, method):
        self.frozen = False
        self.method = method 
        self.__repr__ = lambda self=self: "[conditional] " + str(method)
    def __call__(self, *args, **kwargs):        
        if self.frozen: return None        
        return self.method ( *args, **kwargs )
    def freeze (self):
        self.frozen = True        
    def thaw(self):
        self.frozen = False
        
def import_dict_as_attributes (obj, dic, defaults={}):
    for d in defaults: obj.__dict__[d] = defaults[d]
    for a in dic: obj.__dict__[a] = dic[a]