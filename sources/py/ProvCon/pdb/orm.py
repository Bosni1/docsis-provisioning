#!/bin/env python
# -*- coding: utf8 -*-
import contextlib
import cStringIO
import pg, re
import exceptions

__all__ = ["CFG", "Field", "Table", "Record", "RecordList"]

class ORMError(exceptions.BaseException): pass

class CFG:
    class DB:
        HOST = "localhost"
        PORT = 5432
        DBNAME = "Provisioning"
        ROLE = None
        PASS = None
        SCHEMA = "pv"        
    class RT:
        DATASCOPE = 0
    class tCX(pg.DB):
        instanceCount = 0
        instance = None
        def __init__(self):
            pg.DB.__init__(self, dbname=CFG.DB.DBNAME, user=CFG.DB.ROLE, host=CFG.DB.HOST)            
            CFG.tCX.instanceCount += 1
            print "tCX init [%d]" % self.instanceCount
            idmap = {}
            tableinfo = self.query ( "SELECT * FROM {0}.table_info".format(CFG.DB.SCHEMA) ).dictresult()
            for ti in tableinfo:
                #print "TABLE {name}  == {objectid}".format(**ti)
                with Table.New ( ti['name'], **ti ) as t:
                    columninfo = self.query ( "SELECT * FROM {0}.field_info WHERE classid = {objectid}".format(CFG.DB.SCHEMA, **ti)).dictresult()
                    for ci in columninfo:                        
                        t.addField ( Field (size=ci['length'], **ci) )
                    idmap[t.objectid] = t
                    
            #import foreign key relationships
            for t in Table.__all_tables__.values():
                for f in t.fields:
                    if f.reference: 
                        #print "{0.name}.{1.name} -> references {1.reference}".format (t,f)
                        f.reference = idmap[f.reference]
                        #print "reference ", f.path, 'to', t.objectid, '-', t.name
                        idmap[t.objectid].reference_child.append ( (t, f) )
                        idmap[t.objectid].reference_child_hash[(t.name, f.name)] = (t,f)
                    if f.arrayof:
                        f.arrayof = idmap[f.arrayof]
            self.instance = self
        
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
                if len(content) == 1 and curitem == '':
                    yield []
                else:                
                    yield content
                curitem = ''
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
            self.id = kkw.get("objectid", None)

            for k in kkw:
                if k not in self.__dict__: self.__dict__[k] = kkw[k]
            
            
            
        except KeyError, e:
            kwname, = e.args
            raise Field.IncompleteDefinition ( "missing: '%s' in field definition." % kwname )
    
    def __repr__(self):
        return "{0} : {1}".format (self.name, self.type)

    
    def val_sql2py(self, sqlval):
        """convert the value returned by pg into a python variable"""
        if self.isarray:
            return text_to_array (sqlval, self.arraysize-1)
        return sqlval
    
    def val_py2sql(self, pyval):
        """convert a python variable into something we can insert into an pgSQL statement"""
        if self.isarray:
            return array_as_text (pyval)
        elif isinstance(pyval, str):
            return str(pyval.encode('utf-8'))
        else:
            return str(pyval)
    
    def val_py2txt(self, pyval):
        if self.isarray:
            return "array:" + array_as_text(pyval)
        if pyval is None:
            return ''
        elif isinstance(pyval, str):
            return str(pyval.encode('utf-8'))
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
    def New(tablename, *args, **kwargs):
        Table.__all_tables__[tablename] = Table(tablename, *args, **kwargs)
        yield Table.__all_tables__[tablename]
    
    @staticmethod
    def Get(name):
        return Table.__all_tables__.get (name, None)
        
    def __init__(self, tablename, inherits="object", **kwargs):
        self.name = tablename
        self.id = kwargs.get("objectid", None)
        self.objectid = kwargs.get("objectid", None)
        self.fields = []
        self.fields_hash = {}
        self.reference_child = []
        self.reference_child_hash = {}
        self.schema = kwargs.get ( "schema", CFG.DB.SCHEMA )
        self.label = kwargs.get ( "label", self.name )
        
    def addField(self, field):
        assert isinstance(field, Field)
        if field.lp < 0: field.lp = len(self.fields)
        self.fields.append (field)
        self.fields_hash[field.name] = field
        self.fields.sort ( lambda x, y: x.lp - y.lp )
        
    def recordList(self, _filter="TRUE", select=[], order="objectid"):
        from_clause = self.schema + "." + self.name + " o LEFT JOIN " + self.schema + ".object_search_txt t ON o.objectid = t.objectid"
        return CFG.CX.query ( "SELECT o.objectid, t.txt as _astxt, o.objectmodification {3} FROM {0} WHERE {1} ORDER BY {2}".format (from_clause, _filter, order, ",".join(select) )).dictresult()

    def recordObjectList(self, _filter="TRUE", select=[], order="objectid"):
        rl = self.recordList(_filter, select, order)
        li = []
        for r in rl:
            rec = Record.EMPTY (self)
            rec.feedDataRow ( r )
            li.append (rec)
        return li
    
    def __iter__(self):        
        return iter(self.fields)            

    def __contains__(self, fname):
        return fname in self.fields_hash
    
    def __getitem__(self, idx):
        if idx in self:
            return self.fields_hash[idx]
        return None

    def __repr__(self):
        return "<TABLE [" + self.schema + "." + self.name + "]>"
    
class Record(object):    
    class RecordNotFound(ORMError): pass

    __default_reference_mode__ = "text"
    
    def __init__(self, **kkw):
        self._isnew = False
        self._hasdata = False        
        self._isinstalled = False
        self._isreference = False
        self._objectid = None
        self._ismodified = False
        self._original_values = {}
        self._modified_values = {}
        self._references = {}
        self._table = None
        self._astxt = None
        self._feed = False
        self._resolvereference = kkw.get("resolvereference", self.__default_reference_mode__)  # none | text | record
        self._reprfunc = kkw.get ( "reprfunc", None )        
        
                
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
                if attrval and not self._feed:
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
        elif attrname.endswith("_REF"):
            fname = attrname[:-4]
            if fname in self._references: return self._references[fname]
        return self.__dict__[attrname]

    def nullify(self):
        self._original_values.clear()
        self._modified_values.clear()
        self._references.clear()
        self._ismodified = False
        self._hasdata = False
        self._astxt = None
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

    def updateReferenceField(self, field):
        if not field.reference: return
        decoded = self.__dict__[field.name]
        if not decoded: self._references[field.name] = None; return
        if self._resolvereference == "none":
            self._references[field.name] = decoded
        elif self._resolvereference == "text":
            try:
                self._references[field.name] = CFG.CX.get ( CFG.DB.SCHEMA + ".object_search_txt",
                                                    {"objectid" : decoded} )['txt']
            except KeyError:
                self._references[field.name] = "<null>"
        elif self._resolvereference == "record":
            self._references[field.name] = Record.ID (decoded)

    
    def feedDataRow(self, row, **kwargs):
        self._feed = True
        self._objectid = row['objectid']
        self._feed = False

        self._original_values.clear()
        for cn in row:
            if cn not in self._table: continue
            field = self._table[cn]
            decoded = field.val_sql2py ( row[cn] )
            self.__dict__[cn] = decoded
            self._original_values[cn] = decoded
            if field.reference:
                self.updateReferenceField(field)

        if '_astxt' in row:
            self._astxt = row['_astxt']
        elif self._reprfunc:
            self._astxt = self._reprfunc (self)
        else:            
            try:
                self._astxt = CFG.CX.get (CFG.DB.SCHEMA + ".object_search_txt", 
                                          { 'objectid' : self._objectid} )['txt']
            except KeyError:
                if self._reprfunc: self._astxt = self._reprfunc (self)
                else: self._astxt = None
        
            
        self._hasdata = True
        self._isnew = False
        self._ismodified = False
        self._modified_values.clear()
        
    
    def read(self):
        if not self._table :
            if not self.setupRecord():
                raise ValueError ( "no _table" )
        if not self._objectid:
            raise ValueError ( "no _objectid" )
        try:
            row = CFG.CX.get ( CFG.DB.SCHEMA + "." + self._table.name, { 'objectid' : self._objectid, 
                                                                         'objectscope' : CFG.RT.DATASCOPE } )
            self.feedDataRow(row)
            
        except pg.DatabaseError, e:
            print e
            raise Record.RecordNotFound("#{0} in {1}".format(self._objectid, self._table.name))
            
        
    def write(self):
        if not self._table: raise ValueError ( "_table is Null" )
        if self._isnew:           
            for m in self._modified_values:
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
                
            rec = CFG.CX.insert ( CFG.DB.SCHEMA + "." + self._table.name,
                            self._modified_values )
            self._objectid = rec['objectid']
            self.read()
        elif self._ismodified:
            for m in self._modified_values:
                print "mod:", m
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
            self._modified_values['objectid'] = self._objectid
            rec = CFG.CX.update ( CFG.DB.SCHEMA + "." + self._table.name,
                                  self._modified_values )
            self.read()        
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
    
    def __repr__(self):
        if self._table:
            return "<record of {0} #{1}> {2}".format (self._table.name, self._objectid,
                                                      self._astxt )
        return "<record>"
    @staticmethod
    def ID(objectid, **kkw):
        rec = Record(**kkw)
        rec.setObjectID(objectid)        
        return rec
    
    @staticmethod
    def EMPTY(tabledef, **kkw):
        rec = Record(**kkw)
        rec.setTable (tabledef)
        rec._isnew = True
        return rec
    
    @staticmethod
    def COPY(record):
        assert isinstance(record, Record)
        pass

    @staticmethod
    def CHILDREN(parentid, reftable, refcolumn, **kwargs):
        limit = kwargs.get ( "limit", None )
        order = kwargs.get ( "order", ['o.objectid'] )
        reprfunc = kwargs.get ( "reprfunc", None )
        gettxt = kwargs.get ( "gettxt", True )
        select = kwargs.get ( "select", ["*"] )
        if limit:
            limit = "OFFSET {0} LIMIT {1}".format ( *limit )
        else:
            limit = ""
        order = ",".join(order)
        select = ",".join(select)
        if gettxt:
            gettxtq = ("LEFT JOIN pv.object_search_txt t ON t.objectid = o.objectid", ", t.txt as _astxt" )
        else:
            gettxtq = ( "", "" )
        query = "SELECT {6}{8} FROM {5}.{0} o {7} WHERE \"{1}\" = '{2}' ORDER BY {3} {4}".format (
            reftable, refcolumn, int(parentid), order, limit, CFG.DB.SCHEMA,
            select, gettxtq[0], gettxtq[1] )
        rowset = CFG.CX.query ( query ).dictresult()
        table = Table.Get ( reftable )
        for row in rowset:
            record = Record.EMPTY (table, reprfunc = reprfunc )
            record.feedDataRow ( row )
            yield record

    
class ReferencedRecord(Record):
    pass

class RecordList(list):
    def __init__(self, table, _filter="TRUE", select=[], order="objectid"):
        list.__init__(self)
        self.table = table
        self._filter = _filter
        self.select = select
        self.order = order
        self.hash_id = {}
    
    def reload(self):
        list.__init__(self)
        print self.table, self.select
        self += self.table.recordObjectList (self._filter, self.select, self.order)
        self.hash_id.clear()
        for r in self: self.hash_id[r.objectid] = r
    def getid(self, objectid):
        return self.hash_id[objectid]
    
def StartupDatabaseConnection():
    print "DB STARTUP"
    CFG.CX = CFG.tCX.instance or CFG.tCX()

StartupDatabaseConnection()

#table = Record.ID(3)
#print table


#for r in Record.CHILDREN (3, "field_info", "classid", gettxt=False):
    #print r
    