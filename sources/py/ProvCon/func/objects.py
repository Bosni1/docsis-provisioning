#!/bin/env python
##$Id:$

class AttrDict(dict):
    def __init__(self):
        dict.__init__(self)
        self.__dict__['ordered'] = []
        
    def __setattr__(self, attrname, attrval):        
        if attrname in self.__dict__:
            self.__dict__[attrname] = attrval
        else:        
            if attrname not in self.ordered:
                self.ordered.append (attrname)
            self[attrname] = attrval
                            
    def __getattr__(self, attrname):
        try:
            if attrname in self.__dict__:
                return self.__dict__[attrname]
            else:
                return self[attrname]
        except KeyError:
            return None
        
    def inorder(self):
        for attrname in self.ordered:
            yield (attrname, self[attrname])
            