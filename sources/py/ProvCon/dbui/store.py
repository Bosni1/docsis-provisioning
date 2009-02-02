##$Id$
import orm, meta

class Store:
    def __init__(self):
        self.__recordlists__ = {}
        
    def init__city(self):
        if self.exists ("city"):
            self.reload("city")
        else:
            self.__recordlists__["city"] = orm.RecordList ( meta.Table.Get ("city"),
                                                            select=["name", "handle"], order='name' )
            
    def __getattr__(self, attrname):
        if attrname in self.__dict__:
            return self.__dict__[attrname]
        elif attrname in self.__recordlists__:
            return self.__recordlists__[attrname]: