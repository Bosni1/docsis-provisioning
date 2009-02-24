"""
The heart of the database abstraction layer. It defines the L{Record} class
which represents the database at the table row level.

The Record objects are designed to work with tables of a very specific structure. Current 
implementation involves heavy usage of PostgreSQL features such as table-inheritance and
C{SELECT ... FROM ONLY ...} .

The assumptions may be roughly summarized as follows:

   1. All tables are subtables (subclasses, descendants) of a table named C{object} with this
   signature:
      - objectid : int8 PRIMARY KEY
      - objecttype : varchar (I{name of the actual table})
      - objectcreation, objectmodification : timestamp
      - objectscope : int2
   2. All foreign keys reference the C{objectid} column in the referenced table.
   3. Multiple-column references are not supported (simplicity).
   
I{for more specific information on the database structure refer to the database docs}      

Usage
=====

Recommended usage pattern of the Record class:

   >>> newRecord = Record.EMPTY ( "customer" )
   >>> newRecord.objectid
   None
   >>> newRecord.email = "customer@server.com"
   >>> newRecord.telephone = "001 123 445 444"
   >>> newRecord.write()
   >>> newRecord.objectid
   1554
   >>> oldRecord = Record.ID ( 1554 )
   >>> oldRecord.ofTable ( "customer" )
   True
   >>> oldRecord.email = "customer@customers.com"
   >>> oldRecord.isModified
   True
   >>> oldRecord.email
   'customer@customers.com'
   >>> oldRecord.read()
   >>> oldRecord.isModified
   False
   >>> oldRecord.email
   'customer@server.com'
   >>> oldRecord.setObjectID(1667)
   >>> oldRecord.email
   'othercustomer@server.com'
   >>> oldRecord.delete()
   

"""

from ProvCon.dbui.database import CFG
import ProvCon.dbui.database as db
from ProvCon.func import eventemitter
from errors import ORMError
from ProvCon.dbui.meta import Table
import pg
import cStringIO



__revision__ = "$Revision$"

class Record(eventemitter):
    """    
    A single row in the database. 

    Attributes
    ==========
    
    A Record object is a object-mapping of rows of database data. The API allows accessing
    column values in one og two convenient ways:
    
    C{aRecord.I{columnname}}
    
    C{aRecord["I{columnname}"]}
    
    
    A Record object is set up using the meta-data in a L{Table<ProvCon.dbui.meta.table.Table>} object.
    
    All internal field names start with an '_' underscore character to avoid name clashes with
    column names. Column names that start with an underscore will not  be accessible.
        
    The getattr and setattr methods are overridden to provide the following functionality:
       1. changing the _objectid attribute causes the object to be read from the database (this
       is wrapped be the setObjectID method.
       
       2. changing the _table attribute causes the record to be reset as an empty record
       of the newly set table
       
       3. special attributes PP_* can be used to get a nice textual representation of the record             
           - PP_TABLE prints a tabular representation of the record.
           
       4. attributes named <field_name>_REF return the Record referenced by the field.
           
           >>> aCustomer.location_REF 
           aLocationRecordObject
    
    References
    ==========
    
    There are three modes in which referencing columns may be treated:
       1. B{none}: do nothing, leave the objectid as the column value
       2. B{text}: I{columnname}_REF returns a textual representation of the referenced record
       3. B{record}: I{columnname}_REF holds the actual referenced record
       
    Record.__default_reference_mode__ is the global default mode of resolving references.
    Object-specific mode may be passed to the record constructor with the C{resolvereference}
    keyword argument.
    
    objectid, _objectid, setobjectID
    ================================
    
    Perhaps the most confusing part of the Record object is the way 'objectid' is handled.
    
    The _objectid attribute always holds the current objectid, and setting it to a value triggers
    one of two actions:
       - if the value is not None, and is different from the current value, the record is read
       from the database,
       - if the value is None, the record is reset as a new record (isNew returns True)
    
    The third possibility is - nothing happens, when the given value is the same as the current
    one, or the _feed attribute is set to True (meaning the record is fed data via the feedDataRow
    function).
    
    The C{setObjectID} method is an accessor to the _objectid attribute.
    
       >>> aRecord._objectid = 1
       >>> aRecord.setObjectID(1)
    
    are equivalent.
    
    The C{objectid} attribute holds the current record value of the C{objectid} columns. Modifying
    it marks the record as I{modified} and the new objectid will be written to the database on the
    next C{write}. B{DO NOT DO THIS, IT IS EVIL, IT MAY KILL YOU}!
           
    """
    class RecordIncomplete(ORMError):
        """
        Exception raised when a record does not have a complete definition.
           - not enough parameters to retrieve meta-data, not Table nor ObjectID specified,
           - read operation requested on an empty / new record (no objectid),
           - write operation requested but no table definition installed.        
        """
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
        
        
    class TextRepresentationCache(object):
        def __init__(self):
            self.cache = {}
            self.db = CFG.tCX
        
        def __getitem__(self, key):
            value = None
            try:
                value = self.cache[key]
            except KeyError:
                try:
                    value = CFG.CX.get ( CFG.DB.SCHEMA + ".object_search_txt",
                                         {"objectid" : key} )['txt']
                    self.cache[key] = value
                except pg.DatabaseError, e:
                    raise Record.DataQueryError ( "Error retrieving text value for object.", 
                                              "OBJECT[{0}]".format (key),
                                              e )
            return value
        
        def __delitem__(self, key):
            try:
                del self.cache[key]
            except KeyError:
                pass
            
    
    __default_reference_mode__ = "text"  # none | text | record
    
    DB = CFG.tCX
    TextCache = TextRepresentationCache()
    
    def __init__(self, **kkw):
        """
        Constructor.
        
        Keyword arguments:
           -  C{reprfunc} : string   I{a function object which takes a record object and returns
           its textual representation}
           -  C{resolvereference} : string 
        
        A newly created Record object:
           - has no table definition,
           - has no data.
           
        """
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
        self._astxt = "<NULL>"
        self._feed = False
        self._resolve_mtm = kkw.get ("mtm", False)
        self._resolve_child_ref = kkw.get("children", False)
        self._resolvereference = kkw.get("resolvereference", self.__default_reference_mode__)  # none | text | record
        self._mtm_referencelist = {}
        self._child_referencelist = {}
        self._reprfunc = kkw.get ( "reprfunc", None )        
        
        if 0:
            assert isinstance(self._table, Table)            
                
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
        elif attrname.endswith("_LABEL"):
            fname = attrname[:-6]
            if fname in self._table:
                field = self._table[fname]
                try:
                    self.setFieldStringValue(field.choices_value_hash[attrval])
                except KeyError:
                    return None                
        elif attrname in self._table.mtm_relationships:
            self.addMTMAssociation (attrname, attrval)
        elif attrname[7:] in self._table.mtm_relationships and attrname.startswith("delete_"):
            self.delMTMAssociation (attrname[7:], attrval)
        else:
            #this is a record attribute
            if attrname in self._table:
                self.setFieldValue ( attrname, attrval )
    
    def __getattr__(self, attrname):
        if attrname in self._mtm_referencelist:
            if not self.hasData: return None
            theList = self._mtm_referencelist[attrname]
            if not theList.bound: theList.parentobjectid = self.objectid
            return theList
        elif attrname.endswith('_oids') and attrname[:-5] in self._table.mtm_relationships:
            return self.getMTMAssociation(attrname[:-5])
        #special PP_* attributes return a "pretty printed" representation of the record        
        elif attrname.startswith ("list_"):
            rest = attrname[5:]
            if rest in self._child_referencelist:
                rlist = self._child_referencelist[rest]
                return rlist
            return None
        elif attrname.startswith ("PP_"):
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
            if fname in self._table:
                if not self._table[fname].reference:
                    return None
                if fname not in self._references:
                    self.updateReferenceField ( self._table[fname] )
                return self._references.get(fname, None)
        elif attrname.endswith("_LABEL"):
            fname = attrname[:-6]
            if fname in self._table:
                field = self._table[fname]
                try:
                    return field.choices_label_hash[self.getFieldValue(fname)]
                except KeyError:
                    return None                
        return self.__dict__[attrname]
    
    __getitem__ = __getattr__
    __setitem__ = __setattr__

    def __is_modified(self): 
        return self._ismodified
    isModified = property(__is_modified)
    """C{True} if the record was edited since last read, write"""
    def __is_new(self): 
        return self._isnew
    isNew = property(__is_new)
    """C{True} if the record is new (not yet written to the database, objectid == None)"""
    def __hasdata(self): 
        return self._hasdata
    hasData = property(__hasdata)
    """C{True} if the record holds data read from the database"""
    def __is_installed(self): 
        return self._isinstalled
    isInstalled = property(__is_installed)
    """C{True} if the record has a table schema installed"""

    def enableMTM(self):
        self._resolve_mtm = True
        self.setupMTM()
        
    def disableMTM(self):
        self._resolve_mtm = False
        self._mtm_referencelist.clear()

    def setupMTM(self):
        from ProvCon.dbui.orm import RelatedRecordList
        self._mtm_referencelist.clear()
        for mtm_handle in self._table.mtm_relationships:
            self._mtm_referencelist[mtm_handle] = RelatedRecordList (self._table, mtm_handle)

    def addMTMAssociation(self, mtm_handle, refobjectid):
        if not self.hasData: return
        self._table.addRelatedOID (self.objectid, refobjectid, mtm_handle )
        if self._resolve_mtm:
            self._mtm_referencelist[mtm_handle].reload()

    def delMTMAssociation(self, mtm_assoc_name, refobjectid):
        if not self.hasData: return
        self._table.delRelatedOID (self.objectid, refobjectid, mtm_handle )
        if self._resolve_mtm:
            self._mtm_referencelist[mtm_handle].reload()
        
    def getMTMAssociation(self, mtm_handle):
        if not self.hasData: return []
        return self._table.relatedOIDList (self.objectid, mtm_handle)
    
    def enableChildren(self, exclude=[]):
        self._resolve_child_ref = True
        self.setupChildren(exclude)
        
    def disableChildren(self):
        self._resolve_child_ref = False
        self._child_referencelist.clear()

    def setupChildren(self, exclude=[]):
        from ProvCon.dbui.orm import RecordList
        self._child_referencelist.clear()        
        for child_handle in self._table.reference_child_hash:
            if child_handle in exclude: continue
            t, f = self._table.reference_child_hash[child_handle]
            self._child_referencelist[child_handle] = RecordList (t, select=['*'], order="o.objectid" )
        
    def nullify(self):
        """
        Clear all data. 
        
        Note that _objectid remains unchanged, so after a Record has been nullified, 
        it may be read again.
        
        Do not call on Records that are not yet installed (have no table definition).
        """
        self._original_values.clear()
        self._modified_values.clear()
        self._references.clear()
        for mtm in self._mtm_referencelist:
            self._mtm_referencelist[mtm].parentobjectid = None
        for chl in self._child_referencelist:
            self._child_referencelist[chl].clear()            
        self._ismodified = False
        self._hasdata = False
        self._astxt = "(null)"
        if self._table:            
            for f in self._table:
                self._original_values[f.name] = None                
                        
    def setupRecord(self, vals={}):        
        """
        Import the record structure from the _table object. 
        
        If the record is not installed (no table definition, _table is None), attempt to install
        by querying the database to retrieve the object type.
        
        If both _table and _objectid are empty, raise an exception.
        
        On success the record has attributes corresponding to database table columns, and
        isInstalled returns True.
        """
        from ProvCon.dbui.orm import RelatedRecordList
        if not self._table:
            if not self._objectid:
                raise Record.RecordIncomplete()
            else:
                try:
                    row = CFG.CX.get ( CFG.DB.SCHEMA + ".object", { 'objectid' : self._objectid, 
                                                                    'objectscope' : CFG.RT.DATASCOPE } )
                except pg.DatabaseError, e:
                    raise Record.DataManipulationError ( "Error retrieving base object ID#{0}".format( self._objectid ),
                                                         "get {1}.object ({0})".format (self._objectid, CFG.DB.SCHEMA) )

                self._table = Table.Get ( row['objecttype'] )

        for f in self._table:
            self.__dict__[f.name] = vals.get(f.name, None)
            self._original_values[f.name] = self.__dict__[f.name]
        
        if self._resolve_mtm:
            self.setupMTM()
        if self._resolve_child_ref:
            self.setupChildren()
            
        self._isinstalled = True
        self._ismodified = False
        self._hasdata = False
        return True
    
    def clearRecord(self):
        """
        Discard all data and the table definition.
        """            
        if self._isinstalled:
            for f in self._table:
                try:
                    del self.__dict__[f.name]
                except KeyError:
                    pass
            self._original_values.clear()
            self._modified_values.clear()
            self._mtm_referencelist.clear()
            self._child_referencelist.clear()
            self._hasdata = False
            self._ismodified = False
            self._hasdata = False
            self._isnew = False
            self._objectid = None
            self._isinstalled = False
            self._astxt = "(null)"

    def setFieldValue (self, fieldname, fieldvalue):
        """
        Set a field to a python-object value.
        
        It is safe to use C{aRecord.I{fieldname} = I{fieldvalue}} instead.
        
        @type fieldname:  string
        @param fieldname: name of the field
        @type fieldvalue: object
        @param fieldvalue:new value        
        """
        if fieldname in self._table:
            self._modified_values[fieldname] = fieldvalue
            self.__dict__[fieldname] = fieldvalue
            self._ismodified = True
            
    def setFieldStringValue (self, fieldname, fieldstrvalue):
        """
        Set a field to a parsed string representation of the value.

        @type fieldname:  string
        @param fieldname: name of the field
        @type fieldstrvalue: string
        @param fieldstrvalue:new string value                
        """
        if fieldname in self._table:
            pyval = self._table[fieldname].val_txt2py ( fieldstrvalue )
            self.setFieldValue (fieldname, pyval )

    def getFieldValue (self, fieldname):
        """
        Get a python value for a particular field.
        It is safe to use C{aRecord.I{fieldname}} instead.
        
        @type fieldname:  string
        @param fieldname: name of the field        
        
        @rtype:  object
        @return: value of the field
        """
        return self._modified_values.get(fieldname, None) or self._original_values[fieldname]

    def getFieldStringValue (self, fieldname):
        """
        Get a string representation of a field value.
        @type fieldname:  string
        @param fieldname: name of the field        

        @rtype:  string
        @return: string value of the field
        """
        v = self.getFieldValue ( fieldname )
        return self._table[fieldname].val_py2txt ( v )    

    def updateReferenceField(self, field):
        """
        Read data referenced by one of the fields in the given reference resolving mode.
        """        
        if not field.reference: return
        decoded = self.__dict__[field.name]
        if not decoded: self._references[field.name] = None; return
        if self._resolvereference == "none":
            self._references[field.name] = decoded
        elif self._resolvereference == "text":
            self._references[field.name] = self.TextCache[decoded] or "(null)"                                              
        elif self._resolvereference == "record":
            self._references[field.name] = Record.ID (decoded)

            
    def feedDataRow(self, row, **kwargs):
        """
        Fill record data structures from a dictionary object.

        This function may be used to fill a Record object with data bypassing all internal
        record mechanisms. It is useful, when Record objects must be created in great numbers
        from data obtained by other means.
        
        Creating a large number of Record objects involves a significant performance penalty
        (up to 3 SELECTs for each record).
        
        @type row: dict
        @param row: a dictionary of database row (column name -> value).                
        """        

        self.nullify()
        
        #avoid automatic call to "read" after _objectid changes        
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
        
        #if _astxt was not provided with the data, _reprfunc is not set,
        #get the text from database
        if '_astxt' in row:
            self._astxt = row['_astxt']
        elif self._reprfunc:
            self._astxt = self._reprfunc (self)
        else:            
            self._astxt = self.TextCache[self._objectid] or "(none)"
                
        if self._resolve_child_ref:
            for child_handle in self._child_referencelist:
                t, f = self._table.reference_child_hash[child_handle]                
                self._child_referencelist[child_handle].filter = f.name + " = '" + str(row['objectid']) + "'"
                self._child_referencelist[child_handle].reload()
                
        self._hasdata = True
        self._isnew = False
        self._ismodified = False
        self._modified_values.clear()
            
        
    def read(self):
        """
        Read a row of data from the database.
        
        If there is no _table definition, call L{setupRecord} to attempt to fetch it based on the
        _objectid.
        """
        if not self._objectid:
            raise Record.RecordIncomplete()

        if not self._table :
            #prepare meta-data if not available
            if not self.setupRecord():
                raise Record.RecordIncomplete()
        try:
            row = CFG.CX.get ( CFG.DB.SCHEMA + "." + self._table.name, { 'objectid' : self._objectid, 
                                                                         'objectscope' : CFG.RT.DATASCOPE } )            
        except pg.DatabaseError, e:                        
            raise Record.RecordNotFound(self._objectid, e)
        
        self.feedDataRow(row)
        
    def write(self):
        """
        Insert or update the record into the database.

        Inserts a new record or updates an existing, locally modified record.
        The record is then re-read to reflect all changes done on the server-side (triggers etc.)
        
        EMITS        
           - B{record_added} (self)
           - B{record_updated} (self)
        """
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

                #print "Record # {0} inserted into {1}.".format(self._objectid, self._table.name)
                self.raiseEvent ( "record_added", self )
                
            except pg.DatabaseError, e:
                print "Error inserting record."
                raise Record.DataManipulationError ( "Inserting a new record into '{0}'".format(self._table.name),
                                                     str(self._modified_values),
                                                     e)
        elif self._ismodified:
            
            for m in self._modified_values:                
                self._modified_values[m] = self._table[m].val_py2sql(self._modified_values[m])
                
            self._modified_values['objectid'] = self._objectid
            del self.TextCache[self._objectid]
            try:
                rec = CFG.CX.update ( CFG.DB.SCHEMA + "." + self._table.name,
                                      self._modified_values )
                self.read()                
                self.raiseEvent ( "record_saved", self )
            except pg.DatabaseError, e:
                print "Error updating record"
                raise Record.DataManipulationError ( "Updating record {1} of '{0}'".format(self._table.name, self._objectid),
                                                     str(self._modified_values),
                                                     e)
                
    
    def delete(self):
        """
        Delete the record from the database.
        
        EMITS        
           - B{record_deleted} (self)
        """
        if not self.isNew:
            #We do not check the hasData property, so we can use this function to delete records
            #without reading them first.
            #TODO: this is stupid and unclean, change it
            try:
                CFG.CX.delete ( CFG.DB.SCHEMA + ".object", { 'objectid' : self._objectid } )
                self.clearRecord()
                self.raiseEvent ( "record_deleted", self )
            except pg.DatabaseError, e:
                raise Record.DataManipulationError ( "Deleting record {1} of '{0}'".format(self._table.name, self._objectid),
                                                     "",
                                                     e)
                                        
    def setObjectID(self, objectid):
        """
        Set the _objectid. (see class docstring)
        @type objectid: integer
        @param objectid: new object id
        """
        self._objectid = objectid
        
    def setTable(self, tabledef):
        """
        Set the table definition (meta-data).
        
        @type tabledef: string or L{Table}
        @param tabledef: name of the table, or a Table object
        """
        if isinstance(tabledef, str):
            self._table = Table.Get ( tabledef )
        elif isinstance(tabledef, Table):
            self._table = tabledef
        else:
            raise ValueError ("table - must be table name or Table instance." )    
        
    def ofTable(self, tablename):
        """
        Check the name of the currently installed table definition.
        
        
        @type tablename: string
        @param tablename: name to check
        
        @rtype: bool
        @return: is the currently set table definition is of a table named C{tablename}
        """
        return tablename == self._table.name
    
    def getData(self):
        """
        Return record data as a C{dict}.
        
        @rtype: dict
        @return: current record data as a columnname -> value dictionary
        """
        data = {}
        data.update ( self._original_values, self._modified_values )
        return data
    
    def __repr__(self):
        if self._table:
            return "<{1}> {2}".format (self._table.name, self._objectid,
                                                      self._astxt )
        return "<record>"    

    def __str__(self):
        try:
            return self._astxt
        except AttributeError:
            return "<empty record>"
    
    @classmethod
    def ID(cls,objectid, **kkw):
        """
        Create and load a record with the given objectid.

        @type objectid: integer
        @param objectid: id of the object to load
           None - new record
           
        @rtype: Record    
        """
        rec = cls(**kkw)
        rec.setObjectID(objectid)        
        return rec
    
    @classmethod
    def EMPTY(cls, tabledef, **kkw):
        """
        Create a new (empty) record of given table.

        @type tabledef: string or L{Table}
        @param tabledef: name of the table, or a Table object
        
        @rtype: Record            
        """
        rec = cls(**kkw)
        rec.setTable (tabledef)
        rec._isnew = True
        return rec
    
    @classmethod
    def COPY(cls, record):        
        assert issubclass(record, Record)
        

    @classmethod
    def CHILDREN(cls, parentid, reftable, refcolumn, **kwargs):
        """
        Generator allowing to iterate over child rows.
        
        Generates a collection of records from I{reftable} that reference an object with 
        I{objectid} = "I{parentid}" by the I{refcolumn}.        
        
        keyword arguments: 
           - limit - max number of records, default None
           - order - expression to be used in the ORDER BY clause
           - reprfunc - function to generate _astxt values for each record
           - gettxt - boolean, fetch _astxt from database
           - select - array of fields to select from reftable, default ['*']
           
        @type parentid: integer
        @type reftable: string
        @type refcolumn: string
        
        @param parentid: object id of the parent (referenced) row
        @param reftable: name of the referencing table
        @param refcolumn: name of the referencing column
        
        @rtype: iterator
        @return: iterator over the specifies, referencing rows
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
            gettxtq = ("LEFT JOIN {0}.object_search_txt t ON t.objectid = o.objectid".format(CFG.DB.SCHEMA), ", t.txt as _astxt" )
        else:
            gettxtq = ( "", "" )
        query = "SELECT {6}{8} FROM {5}.{0} o {7} WHERE \"{1}\" = '{2}' ORDER BY {3} {4}".format (
            reftable, refcolumn, int(parentid), order, limit, CFG.DB.SCHEMA,
            select, gettxtq[0], gettxtq[1] )
        rowset = CFG.CX.query ( query ).dictresult()
        table = Table.Get ( reftable )
        for row in rowset:
            record = cls.EMPTY (table, reprfunc = reprfunc )
            record.feedDataRow ( row )
            yield record

    
    @classmethod
    def IDLIST(cls, tablename, **kwargs):
        """
        Return a list of object ids from a given table.
        
        keyword arguments:
           - where
           - order
           - limit
           - offset
        are inserted into the SQL query in appropriate places.
        
        @type tablename: string
        @param tablename: name of the table
        
        @rtype: list
        @returns: list of object ids
        """
        limit = "LIMIT " + kwargs.get ( "limit", "ALL" )                
        offset = "OFFSET " + kwargs.get ( "offset", "0" )
                        
        order = kwargs.get ( "order", ['objectid ASC'] )
        order = ",".join (order)
        where = kwargs.get ( "where", ['TRUE'] )
        where = " AND ".join (where)
        query = "SELECT objectid FROM {0}.{1} WHERE {2} ORDER BY {3} {4} {5}".format (
            CFG.DB.SCHEMA, tablename, where, order, limit, offset )
        rowset = map(lambda x: x[0], CFG.CX.query ( query ).getresult() )
        return rowset
    
    