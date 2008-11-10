#!/bin/env python
# -*- coding: utf8 -*-
import contextlib
import cStringIO
import pg, re
import exceptions

__all__ = ["CFG", "Field", "Table", "Record"]

class ORMError(exceptions.BaseException): pass

class CFG:
    class DB:
        HOST = "localhost"
        PORT = 5432
        DBNAME = "Provisioning"
        ROLE = "kuba"
        PASS = None
        SCHEMA = "pv"
        INFOSCHEMA = "abstract"
    class RT:
        DATASCOPE = 0
    class tCX(pg.DB):
        def __init__(self):
            pg.DB.__init__(self, dbname=CFG.DB.DBNAME, user=CFG.DB.ROLE)
            idmap = {}
            tableinfo = self.query ( "SELECT * FROM abstract.class").dictresult()
            for ti in tableinfo:
                with Table.New ( ti['name'] ) as t:
                    columninfo = self.query ( "SELECT * FROM abstract.field WHERE classid = %d" % ti['id'] ).dictresult()
                    for ci in columninfo:                        
                        t.addField ( Field (size=ci['length'], **ci) )
                    idmap[t.id] = t
                    
            #import foreign key relationships
            for t in Table.__all_tables__.values():
                for f in t.fields:
                    if f.reference: 
                        f.reference = idmap[t.id]
                        idmap[t.id].reference_ch.append ( (t, f) )
                        idmap[t.id].reference_ch_hash[(t.name, f.name)] = (t,f)
    CX = None

def array_as_text(arr):
    if isinstance(arr, list):
        return "{" + ",".join(map(array_as_text, arr)) + "}"
    else:
        if arr is None: return ''
        else: return str(arr)

def text_to_array(text, depth):
    def inside_array(t):
        bracestate = 0
        content = []
        curitem = ''
        prev = None
        for char in t:
            escaped = prev == '\\'
            if char == '}' and not escaped: bracestate -= 1
            if char == '{' and not escaped: 
                bracestate += 1
                if bracestate == 1: continue
            
            if bracestate == 0:
                content.append ( curitem )
                curitem = ''
                yield content
                content = []      
                continue
            
            if char == ',' and prev != '\\' and bracestate == 1:                
                content.append ( curitem )
                curitem = ''
                continue
            
            if bracestate >= 1: 
                #if char != '\\' or escaped:
                curitem += char            
                       
            prev = char
    if text is None or len(text) == 0: return None
    arr = list(inside_array(text))[0] 
    if depth > 0: return map( lambda x: text_to_array(x, depth-1), arr )
    else: return arr
                   
    
        
class Field(object):
    class IncompleteDefinition(ORMError): pass
        
    def __init__(self, name=None, type='text', size=-1, ndims=0, **kkw):
        try:            
            ndims = ndims or kkw.get('ndims', 0)
            self.name = name or kkw['name']
            self.type = type or kkw['type']
            self.size = size or kkw['size']
            self.lp = kkw.get ( "lp", -1 )
            self.isarray = kkw.get("isarray", ndims > 0)
            self.arraysize = kkw.get("arraysize", ndims )
            self.label = kkw.get("label", self.name)
            self.auto = kkw.get("auto", False)
            for k in kkw:
                if k not in self.__dict__: self.__dict__[k] = kkw[k]
        except KeyError, e:
            kwname, = e.args
            raise Field.IncompleteDefinition ( "missing: '%s' in field definition." % kwname )
    
    def __repr__(self):
        return "{0} : {1}".format (self.name, self.type)

    def val_sql2py(self, sqlval):
        if self.isarray:
            return text_to_array (sqlval, self.arraysize-1)
        return sqlval
    
    def val_py2sql(self, pyval):
        if self.isarray:
            return array_as_text (pyval)
        return str(pyval)
    
    def val_py2txt(self, pyval):
        if self.isarray:
            return "array:" + array_as_text(pyval)
        if pyval is None:
            return ''
        else:
            return str(pyval)
    
    def val_txt2py(self, txtval):
        if self.isarray:
            return text_to_array ( txtval[6:], self.arraysize-1 )
        return txtval
    
    def encode(self, value):
        raise DeprecationWarning
    
    def decode(self, value):
        raise DeprecationWarning
        
class Table(object):
    __special_columns__ = [ "objectid", 
                            "objectmodification", "objectcreation", 
                            "objectdeletion", "objecttype", "objecttypeid",
                            "objectscope" ]
    __all_tables__ = {}
    
    @staticmethod
    @contextlib.contextmanager
    def New(name, *args, **kwargs):
        Table.__all_tables__[name] = Table(name, *args, **kwargs)
        yield Table.__all_tables__[name]
    
    @staticmethod
    def Get(name):
        return Table.__all_tables__.get (name, None)
        
    def __init__(self, name, inherits="object", **kwargs):
        self.name = name
        self.id = kwargs.get("id", None)
        self.fields = []
        self.fields_hash = {}
        self.reference_ch = []
        self.reference_ch_hash = {}

    def addField(self, field):
        assert isinstance(field, Field)
        if field.lp < 0: field.lp = len(self.fields)
        self.fields.append (field)
        self.fields_hash[field.name] = field
        self.fields.sort ( lambda x, y: x.lp - y.lp )
        
    def recordlist(self, _filter="TRUE", order="objectid"):
        from_clause = CFG.DB.SCHEMA + "." + self.name + " o LEFT JOIN " + CFG.DB.SCHEMA + ".object_search_txt t ON o.objectid = t.objectid"
        return CFG.CX.query ( "SELECT o.objectid, t.txt, o.objectmodification FROM {0} WHERE {1} ORDER BY {2}".format (from_clause, _filter, order )).dictresult()
    
    def __iter__(self):        
        return iter(self.fields)            

    def __contains__(self, fname):
        return fname in self.fields_hash
    
    def __getitem__(self, idx):
        if idx in self:
            return self.fields_hash[idx]
        return None
    
class Record(object):
    class RecordNotFound(ORMError): pass
    
    def __init__(self):
        self._isnew = False
        self._hasdata = False        
        self._isinstalled = False
        self._objectid = None
        self._ismodified = False
        self._original_values = {}
        self._modified_values = {}
        self._table = None
        
                
    def __setattr__(self, attrname, attrval):
        if attrname.startswith ( "_" ):
            try:
                valuechange = attrval != self.__dict__[attrname]
            except KeyError:
                self.__dict__[attrname] = None
                valuechange = True
            self.__dict__[attrname]  = attrval
            
            if attrname == "_table" and valuechange:
                self.clearRecord()
                if self._table:
                    self.setupRecord()
            elif attrname == "_objectid" and valuechange:
                if attrval:
                    self.read()
                elif attrval is None:
                    if self._hasdata:
                        self.nullify()
        else:
            if attrname in self._table:
                self.setFieldValue ( attrname, attrval )
                
    def __getattr__(self, attrname):
        if attrname.startswith ("PP_"):
            sio = cStringIO.StringIO()
            rest = attrname[3:]
            if rest == "TABLE":                      
                for f in self._table:                    
                    sio.write( "| {0:24} | {1:40} |\n".format (f.name, self.getFieldValue (f.name) )  )
            return sio.getvalue()
        
        return self.__dict__[attrname]

    def nullify(self):
        self._original_values.clear()
        self._modified_values.clear()
        self._ismodified = False
        self._hasdata = False
        if self._table:            
            for f in self._table:
                self._original_values[f.name] = None                
        
    
    def setupRecord(self, vals={}):        
        if not self._table:
            if not self._objectid:
                raise ValueError ( "_table and _objectid are void." )
            else:
                try:
                    row = CFG.CX.get ( CFG.DB.SCHEMA + ".object", { 'objectid' : self._objectid, 
                                                                    'objectscope' : CFG.RT.DATASCOPE } )
                except pg.DatabaseError:
                    return False
                print row
                self._table = Table.Get ( row['objecttype'] )

        for f in self._table:
            self.__dict__[f.name] = vals.get(f.name, None)
            self._original_values[f.name] = self.__dict__[f.name]
        
        self._isinstalled = True
        self._ismodified = False
        self._hasdata = False
        return True
    
    def clearRecord(self):
        if self._isinstalled:
            for f in self._table:
                del self.__dict__[f.name]
            self._original_values.clear()
            self._modified_values.clear()
            self._hasdata = False
            self._ismodified = False
            self._hasdata = False
            self._isnew = False
            self._objectid = None

    def setFieldValue (self, fieldname, fieldvalue):
        if fieldname in self._table:
            self._modified_values[fieldname] = fieldvalue
            self.__dict__[fieldname] = fieldvalue
            self._ismodified = True
    def setFieldStringValue (self, fieldname, fieldstrvalue):
        if fieldname in self._table:
            pyval = self._table[fieldname].val_txt2py ( fieldstrvalue )
            self.setFieldValue (fieldname, pyval )

    def getFieldValue (self, fieldname):
        return self._modified_values.get(fieldname, None) or self._original_values[fieldname]

    def getFieldStringValue (self, fieldname):
        v = self.getFieldValue ( fieldname )
        return self._table[fieldname].val_py2txt ( v )
    
    def read(self):
        if not self._table :
            if not self.setupRecord():
                raise ValueError ( "no _table" )
        if not self._objectid:
            raise ValueError ( "no _objectid" )
        try:
            row = CFG.CX.get ( CFG.DB.SCHEMA + "." + self._table.name, { 'objectid' : self._objectid, 
                                                                         'objectscope' : CFG.RT.DATASCOPE } )
        except pg.DatabaseError, e:
            print e
            raise Record.RecordNotFound("#{0} in {1}".format(self._objectid, self._table.name))
            
        self._original_values.clear()
        for cn in row:
            if cn not in self._table: continue
            decoded = self._table[cn].val_sql2py ( row[cn] )
            self.__dict__[cn] = decoded
            self._original_values[cn] = decoded
            
        self._hasdata = True
        self._isnew = False
        self._ismodified = False
        self._modified_values.clear()
        
    def write(self):
        if not self._table: raise ValueError ( "_table is Null" )
        if self._isnew:           
            for m in self._modified_values:
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
                
            rec = CFG.CX.insert ( CFG.DB.SCHEMA + "." + self._table.name,
                            self._modified_values )
            self._objectid = rec['objectid']
        elif self._ismodified:
            for m in self._modified_values:
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
            self._modified_values['objectid'] = self._objectid
            rec = CFG.CX.update ( CFG.DB.SCHEMA + "." + self._table.name,
                                  self._modified_values )
            print rec
            
    def delete(self):
        if not self._isnew:
            CFG.CX.delete ( CFG.DB.SCHEMA + ".object", { 'objectid' : self._objectid } )
            self.clearRecord()
            
    def setObjectID(self, objectid):
        self._objectid = objectid
        
    def setTable(self, tabledef):
        if isinstance(tabledef, str):
            self._table = Table.Get ( tabledef )
        elif isinstance(tabledef, Table):
            self._table = tabledef
        else:
            raise ValueError ("table - must be table name or Table instance." )

    def ofTable(tablename):
        return tablename == self._table.name
    
    @staticmethod
    def ID(objectid):
        rec = Record()
        rec.setObjectID(objectid)        
        return rec
    
    @staticmethod
    def EMPTY(tabledef):
        rec = Record()
        rec.setTable (tabledef)
        rec._isnew = True
        return rec
    
    @staticmethod
    def COPY(record):
        assert isinstance(record, Record)
        pass

CFG.CX = CFG.tCX()



