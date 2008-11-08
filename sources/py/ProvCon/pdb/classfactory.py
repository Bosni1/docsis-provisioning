#!/bin/env python

from connection import Abstract, ProvisioningDatabase

class recordstub(object):
    __slots__ = ["rpr"]
    def __init__(self, rpr):
        self.rpr = rpr
    def __repr__(self):
        return self.rpr
    
NEW_RECORD = recordstub("NEW_RECORD")    
NULL_VALUE = recordstub("<NULL>")

class BaseManufacturedClass(object):
    def __init__(self, objectid=NEW_RECORD, **kkw):
        for flname in self.__signature__['fields']:
            self.__dict__[flname] = NULL_VALUE
    
    def _sql_insert(self):
        pass

    def repr_str(self):
        for f in self.__fieldnames__:
            print self.__fields__[f]['label'].ljust(26) + " := " + repr(self.__dict__[f])
    
def ClassFactory (tablename, abstract):
    def removesystemcolumns(abstract):
        rabs = dict(abstract)
        for syscolumn in [ "tableoid", "cmax", "cmin", "xmax", "xmin", "ctid" ]:
            del rabs['fields'][syscolumn]
        return rabs
    signature = removesystemcolumns(abstract[tablename])

    class _dbclass(BaseManufacturedClass):
        __signature__ = signature
        __classname__ = tablename
        __fields__ = signature['fields']
        __fieldnames__ = signature['fields'].keys()
        def __init__(self, *kw, **kkw):
            BaseManufacturedClass.__init__(self, *kw,**kkw)                            
    
    _dbclass.__name__ = tablename[1]
    return _dbclass


class DatabaseProxy(object):
    __abstract__ = None     
    __classes__ = None
    __schema__ = "pv"
    __cnx__ = None

    @staticmethod
    def Initialize():
        DatabaseProxy.__abstract__ = Abstract()
        DatabaseProxy.__classes__ = {}
        DatabaseProxy.__cnx__ = ProvisioningDatabase()
        for (schema, tname) in DatabaseProxy.__abstract__.keys():
            DatabaseProxy.__classes__[tname] = ClassFactory((schema, tname), DatabaseProxy.__abstract__)
            
    @staticmethod
    def QueryDictResult(qry):
        return DatabaseProxy.Query ( qry ).dictresult()
    
    @staticmethod
    def QueryRowResult(qry):
        try:
            return DatabaseProxy.QueryDictResult() [0]
        except IndexError:
            return None

    @staticmethod
    def QueryResult(qry):
        return DatabaseProxy.Query ( qry ).getresult()

    @staticmethod
    def QuerySingleResult(qry, r, c):
        try:
            return DatabaseProxy.QueryResult()[r][c]
        except IndexError:
            return None    

    @staticmethod
    def Query(qry):        
        return DatabaseProxy.__cnx__.query (qry)
        
    @staticmethod
    def Object(objectid):
        objecttype = DatabaseProxy.QuerySingleResult (
            "SELECT objecttype FROM pv.object WHERE objectid = {0:d}".format (objectid)
        )
        if objecttype is None: return None
        return DatabaseProxy.__classes__[objecttype] (objectid)

    @staticmethod
    def New(objecttype):
        return DatabaseProxy.__classes__[objecttype] (NEW_RECORD)
    
DatabaseProxy.Initialize()        
s1 = DatabaseProxy.New ( "subscriber" )
print s1.repr_str()

    
    