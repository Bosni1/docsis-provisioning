#!/bin/env python
##$Id:$

class AttrDict(dict):
    def __setattr__(self, attrname, attrval):        
        if hasattr(self, attrname):
            self.__dict__[attrname] = attrval
        else:        
            self[attrname] = attrval
                            
    def __getattr__(self, attrname):
        try:
            if hasattr(self, attrname):
                return self.__dict__[attrname]
            else:
                return self[attrname]
        except KeyError:
            return None