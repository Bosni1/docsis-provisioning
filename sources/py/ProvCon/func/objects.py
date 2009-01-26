#!/bin/env python
##$Id:$

class AttrDict(dict):
    def __setattr__(self, attrname, attrval):        
        if attrname in self.__dict__:
            self.__dict__[attrname] = attrval
        else:        
            self[attrname] = attrval
                            
    def __getattr__(self, attrname):
        try:
            if attrname in self.__dict__:
                return self.__dict__[attrname]
            else:
                return self[attrname]
        except KeyError:
            return None