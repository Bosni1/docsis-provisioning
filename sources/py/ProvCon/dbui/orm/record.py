from ProvCon.dbui.database import CFG
import ProvCon.dbui.database as db
from ProvCon.func import eventemitter
from errors import ORMError
from ProvCon.dbui.meta import Table
import pg
import cStringIO

class Record(eventemitter):
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
    class RecordIncomplete(ORMError):
        def __repr__(self):
            return """Object-Relation Mapper SQL Error 
- not enough parameters to retrieve meta-data, not Table nor ObjectID specified,
- read operation requested on an empty / new record (no objectid),
- write operation requested but no table definition installed."""
    class RecordNotFound(ORMError): 
        def __init__(self, objectid, pgexception, **kkw):
            ORMError.__init__ (self)
            self.objectid = objectid
            self.pgexception = pgexception
        def __repr__(self):
            return """Object-Relation Mapper
Error retrieving object with objectid = {0.objectid}
API Error: {1}""".format ( self, self.pgexception )
            
    class DataManipulationError(ORMError): 
        def __init__(self, msg, query, pgexception, **kkw):
            ORMError.__init__ (self)
            self.msg = msg
            self.query = query
            self.pgexception = pgexception
            
        def __repr__(self):
            return """Object-Relation Mapper SQL Error 
Query    : {0.query}
Message  : {0.msg}
API Error: {0.pgexception}""".format ( self )     
    class DataQueryError(ORMError): 
        def __init__(self, msg, query, pgexception, **kkw):
            ORMError.__init__ (self)
            self.msg = msg
            self.query = query
            self.pgexception = pgexception
            
        def __repr__(self):
            return """Object-Relation Mapper SQL Error 
Query    : {0.query}
Message  : {0.msg}
API Error: {0.pgexception}""".format ( self )     
        
    
    __default_reference_mode__ = "text"  # none | text | record
    
    def __init__(self, **kkw):
        eventemitter.__init__(self, [ 
            "record_loaded",
            "record_saved",
            "record_added",
            "record_deleted"
        ] )
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
        #special PP_* attributes return a "pretty printed" representation of the record
        if attrname.startswith ("PP_"):
            sio = cStringIO.StringIO()
            rest = attrname[3:]
            if rest == "TABLE":                      
                for f in self._table:                    
                    sio.write( "| {0:24} | {1:40} |\n".format (f.name, self.getFieldValue (f.name) )  )
            return sio.getvalue()
        #special <fieldname>_REF attribute, returns value referenced by the field
        #exactly what is returned is determined by the _resolvereference object attribute
        elif attrname.endswith("_REF"):
            fname = attrname[:-4]
            if fname in self._references: return self._references[fname]
        return self.__dict__[attrname]
    
    __getitem__ = __getattr__
    
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
                raise Record.RecordIncomplete()
            else:
                try:
                    row = CFG.CX.get ( CFG.DB.SCHEMA + ".object", { 'objectid' : self._objectid, 
                                                                    'objectscope' : CFG.RT.DATASCOPE } )
                except pg.DatabaseError, e:
                    raise Record.DataManipulationError ( "Error retrieving base object ID#{0}".format( self._objectid ),
                                                         "get pv.object ({0})".format (self._objectid) )

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
            except pg.DatabaseError, e:
                raise Record.DataQueryError ( "Error retrieving text value for referenced row.", 
                                              "OBJECT[{0._objectid}].{1} -> OBJECT[{2}".format (self, field.path, decoded),
                                              e )
                                              
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
            except pg.DatabaseError, e:
                raise Record.DataQueryError ( "Error retrieving text value current record.", 
                                              "OBJECT[{0._objectid}].{1}".format (self, field.path),
                                              e )
                
            
        self._hasdata = True
        self._isnew = False
        self._ismodified = False
        self._modified_values.clear()
            
        
    def read(self):
        if not self._objectid:
            raise Record.RecordIncomplete()

        if not self._table :
            #prepare meta-data if not available
            if not self.setupRecord():
                raise Record.RecordIncomplete()
        try:
            row = CFG.CX.get ( CFG.DB.SCHEMA + "." + self._table.name, { 'objectid' : self._objectid, 
                                                                         'objectscope' : CFG.RT.DATASCOPE } )
            self.feedDataRow(row)
        except pg.DatabaseError, e:                        
            raise Record.RecordNotFound(self._objectid, e)
            
        
    def write(self):
        if not self._table: raise ValueError ( "_table is Null" )
        if self._isnew:           
            for m in self._modified_values:
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
            
            try:
                rec = CFG.CX.insert ( CFG.DB.SCHEMA + "." + self._table.name,
                                      self._modified_values )
                #this will automatically re-read the data from the db, to take all changes
                #done by triggers and default values into account.
                self._objectid = rec['objectid']

                print "Record inserted into database, objectid = ", self._objectid
                self.emit_event ( "record_added", self )
                
            except pg.DatabaseError, e:
                print "Error inserting record."
                raise Record.DataManipulationError ( "Inserting a new record into '{0}'".format(self._table.name),
                                                     str(self._modified_values),
                                                     e)
        elif self._ismodified:
            for m in self._modified_values:
                print "Modified field:", m
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
            self._modified_values['objectid'] = self._objectid
            try:
                rec = CFG.CX.update ( CFG.DB.SCHEMA + "." + self._table.name,
                                      self._modified_values )
                self.read()
                print "Record updated"
                self.emit_event ( "record_saved", self )
            except pg.DatabaseError, e:
                print "Error updating record"
                raise Record.DataManipulationError ( "Updating record {1} of '{0}'".format(self._table.name, self._objectid),
                                                     str(self._modified_values),
                                                     e)
                
    
    def delete(self):
        if not self._isnew:
            try:
                CFG.CX.delete ( CFG.DB.SCHEMA + ".object", { 'objectid' : self._objectid } )
                self.clearRecord()
                self.emit_event ( "record_deleted", self )
            except pg.DatabaseError, e:
                raise Record.DataManipulationError ( "Deleting record {1} of '{0}'".format(self._table.name, self._objectid),
                                                     "",
                                                     e)
                                        
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
            return "<{1}> {2}".format (self._table.name, self._objectid,
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
    
    