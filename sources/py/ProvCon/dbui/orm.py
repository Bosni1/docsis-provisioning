#!/bin/env python
# -*- coding: utf8 -*-
import contextlib
import cStringIO
import pg, re
import exceptions
from misc import *

__all__ = ["CFG", "Field", "Table", "Record", "RecordList"]

class ORMError(exceptions.BaseException): pass

class CFG:
    """not really a class, just a nice-looking storage for application settings"""
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
        """==tCX==
        Besides being a PostgreSQL connection object, this class builds the ER
        structures used by forms, records, reference editors etc.
        Ideally it should only be instatiated once, the constructor attempts to
        ensure that it is so. The CFG.CX static variable should hold an active
        connection at all times.
        """
        instanceCount = 0
        instance = None
        def __init__(self):
            pg.DB.__init__(self, dbname=CFG.DB.DBNAME, user=CFG.DB.ROLE, host=CFG.DB.HOST)            
            #Attempt to make sure this class is a singleton.
            CFG.tCX.instanceCount += 1
            print "tCX init [%d]" % self.instanceCount
            
            idmap = {}
            tableinfo = self.query ( "SELECT * FROM {0}.table_info".format(CFG.DB.SCHEMA) ).dictresult()
            for ti in tableinfo:
                with Table.New ( ti['name'], **ti ) as t:
                    columninfo = self.query ( "SELECT * FROM {0}.field_info WHERE classid = {objectid}".format(CFG.DB.SCHEMA, **ti)).dictresult()
                    for ci in columninfo:                        
                        t.addField ( Field (size=ci['length'], **ci) )
                    idmap[t.objectid] = t
                    
            #import foreign key relationships
            for t in Table.__all_tables__.values():
                for f in t.fields:
                    #For columns that reference a table_info row, replace the appropriate
                    #values with actual, python-object references
                    if f.reference: 
                        f.reference = idmap[f.reference]
                        #fill the table's children list
                        idmap[t.objectid].reference_child.append ( (t, f) )
                        idmap[t.objectid].reference_child_hash[(t.name, f.name)] = (t,f)
                    if f.arrayof:
                        f.arrayof = idmap[f.arrayof]
            self.instance = self
        
    CX = None



def array_as_text(arr):
    """convert a python list to a textual representation of a postgres array"""
    if isinstance(arr, list):
        return "{" + ",".join(map(array_as_text, arr)) + "}"
    else:
        if arr is None: return ''
        else: return str(arr)

def text_to_array(text, depth):
    """parse a textual postgres array into a python list
    depth - the number of dimensions the array has
    """
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
    """ ==Field==
    Field objects hold meta data about columns in the database.
    They also provide data-conversion services.
    A Field object is created from a row of the 'field_info' table.
    """    
    class IncompleteDefinition(ORMError): 
        """raised when the Field constructor receives incomplete meta-data"""
        pass
    
        
    
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
    """Table objects hold database meta-data"""
    __special_columns__ = [ "objectid", 
                            "objectmodification", "objectcreation", 
                            "objectdeletion", "objecttype", "objecttypeid",
                            "objectscope" ]
    __all_tables__ = {}
    
    @staticmethod
    @contextlib.contextmanager
    def New(tablename, *args, **kwargs):
        """a convenience static method allowing creation of Table objects
        using the 'with' statement'. Not really what the 'with' statement was
        designed for, but looks nice..."""
        Table.__all_tables__[tablename] = Table(tablename, *args, **kwargs)
        yield Table.__all_tables__[tablename]
    
    @staticmethod
    def Get(name):
        return Table.__all_tables__.get (name, None)
        
    def __init__(self, tablename, inherits="object", **kwargs):
        for k in kwargs:
            if k not in self.__dict__: self.__dict__[k] = kwargs[k]                        
        
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
    """==Record==
    Record objects are the heart of the database abstraction layer. A Record object is 
    capabable of manipulating a row of data in a table which fulfills the following
    requirements:
     - is a direct or indirect descendant of the "object" table
     - has an "oid" column
     - is described by a Table object
     All tables that inherit "object" are uniquely identified by the "objectid" column. 
     Moreover, the objectid is unique throughout these tables, and each row(record) 
     holds information about the actual table the record belongs to. It is therefore 
     possible to retrieve a record providing only its objectid.
     
     A Record object's state is defined by the following flags (instance attributes):
     _isnew   ->  record is new, the data is only in memory, objectid is empty
     _hasdata ->  data was read from the database
     _isinstalled ->  the record's table definition was used to initialize object's
                    attributes
    _isreference  ->  the record is a reference column in another record, some columns
                      may be unavailable
    _ismodified     
    
    All object variables have names starting with an '_' character. Field values are 
    stored in instance variables with the same names as fields.
    
    The getattr and setattr methods are overridden to provide the following functionality:
    - changing the _objectid attribute causes the object to be read from the database (this
      is wrapped be the setObjectID method.
    - changing the _table attribute causes the record to be reset as an empty record
      of the newly set table
    - special attributes PP_* can be used to get a nice textual representation of the record      
    - attributes named <field_name>_REF return the Record referenced by the field.
    """
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
            #this is an object attribute
            try:
                valuechange = attrval != self.__dict__[attrname]
            except KeyError:
                self.__dict__[attrname] = None
                valuechange = True
            self.__dict__[attrname]  = attrval
            
            #special treatment for _objectid and _table attributes
            if attrname == "_table" and valuechange:
                #clear ("uninstall") table definition
                self.clearRecord()
                #if a new table definition was give, install it
                if self._table:
                    self.setupRecord()
            elif attrname == "_objectid" and valuechange:
                if attrval and not self._feed:
                    #if the objectid is not empty, is changed, and we 
                    #are not doing a manual data feed, read the record
                    self.read()
                elif attrval is None:
                    #if the objectid is empty, and we have some data 
                    self._isnew = True
                    if self._hasdata:
                        #lose it
                        self.nullify()
        else:
            #this is a record attribute
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
        """Clear all data. Note that _objectid remains unchanged, so
        after a Record has been nullified, it may be read again"""
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
        """This method sets up the internal data structures,
        If the _table attribute is set, the values are written into
        appropriate intance attributes.
        If _table is not set, the object header is read from the the "object" table
        and _table is set based on the "objecttype" column.
        At _table or _objectid must be set before this method is called.
        """
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
        """Clear all data, and lose the _table information."""            
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
            self._isinstalled = False

    def setFieldValue (self, fieldname, fieldvalue):
        """set the field value to a python value"""
        if fieldname in self._table:
            self._modified_values[fieldname] = fieldvalue
            self.__dict__[fieldname] = fieldvalue
            self._ismodified = True
    def setFieldStringValue (self, fieldname, fieldstrvalue):
        """set field value parsed from a string"""
        if fieldname in self._table:
            pyval = self._table[fieldname].val_txt2py ( fieldstrvalue )
            self.setFieldValue (fieldname, pyval )

    def getFieldValue (self, fieldname):
        """get a python value for a particular field"""
        return self._modified_values.get(fieldname, None) or self._original_values[fieldname]

    def getFieldStringValue (self, fieldname):
        """get text value for a particular field"""
        v = self.getFieldValue ( fieldname )
        return self._table[fieldname].val_py2txt ( v )    

    def updateReferenceField(self, field):
        """read a record referenced by one of the fields
        There are 3 modes of resolving references:
        "none" : just the field value is kept in the record, <field>_REF is None
        "text" : the text from "object_search_txt" is stored in <field>_REF
        "record" : a whole Record object is kept in <field>_REF
        the mode is set with the "resolvereference" keyword argument to the
        constructor, default mode is kept in the class variable"""
        
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
        """fill record data from a dictionary object"""
        
        #avoid calling "read" after changing the _objectid
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
        
        #if _astxt was not provided with the data, _reprfunc is not set,
        #get the text from database
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
        if not self._objectid:
            raise ValueError ( "no _objectid" )

        if not self._table :
            #prepare meta-data if not available
            if not self.setupRecord():
                raise ValueError ( "no _table" )
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
            #this will automatically re-read the data from the db, to take all changes
            #done by triggers and default values into account.
            self._objectid = rec['objectid']
            #self.read()
            print rec
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
        """create a new record from objectid"""
        rec = Record(**kkw)
        rec.setObjectID(objectid)        
        return rec
    
    @staticmethod
    def EMPTY(tabledef, **kkw):
        """create a new record of given type"""
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
        """Generate a collection of records from "reftable"
        that reference an object with objectid = "parentid" by
        the "refcolumn".
        additional arguments: 
        limit - max number of records, default None
        order - expression to be used in the ORDER BY clause
        reprfunc - function to generate _astxt values for each record
        gettxt - boolean, fetch _astxt from database
        select - array of fields to select from reftable, default ['*']
        """
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

    
    @staticmethod
    def IDLIST(tablename, **kwargs):
        limit = kwargs.get ( "limit", None )
        if limit: limit = "LIMIT " + str(limit)
        else: limit = ""
        offset = kwargs.get ( "offset", None )
        if offset: offset = "OFFSET " + str(offset)
        else: offset = ""
        
        order = kwargs.get ( "order", ['objectid ASC'] )
        order = ",".join (order)
        where = kwargs.get ( "where", ['TRUE'] )
        where = " AND ".join (where)
        query = "SELECT objectid FROM {0}.{1} WHERE {2} ORDER BY {3} {4} {5}".format (
            CFG.DB.SCHEMA, tablename, where, order, limit, offset )
        rowset = map(lambda x: x[0], CFG.CX.query ( query ).getresult() )
        return rowset
        

        
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
        return self
    
    def getid(self, objectid):
        return self.hash_id[objectid]

class OIDSearchList(list):
    def __init__(self, *args, **kwargs):
        list.__init__ (self)
        self.objecttypes = kwargs.get ( "objecttypes", ["object"] )                
        
        self.limit = kwargs.get ( "limit", None )
        if self.limit: self.limit = "LIMIT %d" % self.limit
        else: self.limit = ""
        
        self.orderby = kwargs.get ( "orderby", ["o.objectid"] )
        self.objectid_hash = {}
        
    def search (self, expression):
        list.__init__(self)
        res = CFG.CX.query ( """SELECT t.objectid, t.txt, o.objecttype 
        from {0}.object_search_txt t inner join {0}.object o on t.objectid = o.objectid
        where o.objectscope = {1} AND o.objecttype IN ({3}) AND t.txt ILIKE $str${2}$str$
        ORDER BY {4}""".format 
        ( CFG.DB.SCHEMA,
          CFG.RT.DATASCOPE,
          expression,
          ",".join(map(lambda o: "'%s'" % o, self.objecttypes) ),
          ",".join(self.orderby))).dictresult()
        print res
        self += map (lambda r: r['objectid'], res )
        for r in res: self.objectid_hash[r['objectid']] = r
    
    def get(self, objectid):
        return self.objectid_hash[objectid]
    
    def resolve(self, objectid):
        if objectid in self.objectid_hash:
            self.objectid_hash[objectid] = Record.ID ( objectid )
        
    def resolveall(self):
        for objid in self: self.resolve(objid)
        
def StartupDatabaseConnection():
    print "DB STARTUP"
    CFG.CX = CFG.tCX.instance or CFG.tCX()


StartupDatabaseConnection()
    