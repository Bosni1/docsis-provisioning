#!/bin/env python

import pg

raise DeprecationWarning

class Abstract(dict):
    instance = None
    def __new__(cls, *args, **kargs):        
        if cls.instance is not None: return cls.instance
        else: 
            cls.instance = dict.__new__(cls, *args, **kargs)            
            cls.instance.full = False
            return cls.instance
    
    def __init__(self, pvdb=None):
        dict.__init__(self)        
        if not self.full:
            if pvdb is None: db = ProvisioningDatabase()
            else: db = pvdb
            db.abstract(self)
            self.full = True
            if pvdb is None: db.close()
        
        

class ProvisioningDatabase(pg.DB):
    def __init__(self):
        pg.DB.__init__ (self, dbname="Provisioning", user="kuba" )
        
    def abstract(self, ab):        
        qr = self.query ( "SELECT * FROM abstract.class" ).dictresult()
        for t_abs in qr:
            ab[(t_abs['schema'], t_abs['name'])] = t_abs
            ab[(t_abs['schema'], t_abs['name'])]['fields'] = {}
            
        qr = self.query ( "SELECT t.schema as sname, t.name as tname, f.* FROM abstract.field f inner join abstract.class t ON t.id = f.classid" ).dictresult()
        for f_abs in qr:
            ab[(f_abs['sname'], f_abs['tname'])]['fields'][f_abs['name']] = f_abs
        return ab


