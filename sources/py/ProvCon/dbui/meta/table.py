from ProvCon.dbui.database import CFG
import contextlib

class Table(object):
    """    
    Table objects hold database tables meta-data.

    Each Table objects is created based on a record form the I{table_info} table. 
    """
        
    __special_columns__ = [ "objectid", 
                            "objectmodification", "objectcreation", 
                            "objectdeletion", "objecttype", "objecttypeid",
                            "objectscope" ]
    """Names of I{special} columns (inherited from I{object})"""
    
    __all_tables__ = {}
    
    @classmethod
    @contextlib.contextmanager
    def New(cls, tablename, *args, **kwargs):
        """
        A convenience static method allowing creation of Table objects using the 'with' statement'. 
        Not really what the 'with' statement was designed for, but looks nice...

           >>> with Table.New ('tablename', **table_info_row) as t:
           ...    t.fields = []

        @type tablename: str
        @param tablename: name of the table to map
        
        @rtype: context
        """
        Table.__all_tables__[tablename] = Table(tablename, *args, **kwargs)
        yield Table.__all_tables__[tablename]
    
    @staticmethod
    def Get(name):
        """
        Get the I{named} Table object.
        
        @type name: str
        @rtype: Table
        """
        return Table.__all_tables__.get (name, None)
        
    def __init__(self, tablename, inherits="object", **kwargs):
        """        
        @type tablename: str
        @type inherits: str
        @rtype: Table
        """
        for k in kwargs:
            if k not in self.__dict__: self.__dict__[k] = kwargs[k]                        
        
        self.name = tablename
        self.id = kwargs.get("objectid", None)
        self.objectid = kwargs.get("objectid", None)
        self.fields = []
        self.fields_hash = {}
        self.reference_child = []
        self.reference_child_hash = {}
        self.mtm_relationships = {}
        self.schema = kwargs.get ( "schema", CFG.DB.SCHEMA )
        self.label = kwargs.get ( "label", self.name )
    
    def fieldCount(self):
        """
        Get the number of non-special fields in the table.
        @rtype: int
        """
        return len ( filter (lambda f: not f.isSpecial(), self.fields ) )
    
    def addField(self, field):        
        """
        Add a field to this table.
        @type field: Field        
        """
        if field.lp < 0: field.lp = len(self.fields)
        self.fields.append (field)        
        self.fields_hash[field.name] = field
        field.table = self
        self.fields.sort ( lambda x, y: x.lp - y.lp )
        
    def recordCount(self):
        """
        Get the total number of records in this table.
        @rtype: int
        """
        return CFG.CX.query ( "SELECT count(*) as recordCount FROM {0}.{1} WHERE objectscope={2}".format(
            CFG.DB.SCHEMA, self.name, CFG.RT.DATASCOPE )).dictresult()[0]['recordCount']

    def relatedOIDList (self, parentoid, mtm_handle):
        relname, tablename, my_pointer, ref_pointer, referenced_table = self.mtm_relationships[mtm_handle]
                
        result = CFG.CX.query ( "SELECT {2} as objectid FROM {0}.{1} WHERE {3} = '{4}'".format(
            CFG.DB.SCHEMA, tablename, ref_pointer, my_pointer, parentoid ) )
        return map(lambda x: x['objectid'], result.dictresult() )

    def relatedRecordList (self, parentoid, mtm_handle, recordclass=None):
        from ProvCon.dbui.orm import Record
        
        oidlist = self.relatedOIDList(parentoid, mtm_handle)        
        recordclass = recordclass or Record
        return map (lambda x: recordclass.ID(x), oidlist)

    def recordList(self, _filter="TRUE", select=['0'], order="objectid"):
        """
        Get results of a SELECT query.
        
        @type _filter: str
        @type select: str
        @type order: str
        
        @param _filter: an expression to use in the WHERE clause,
        @param select: an expression to append to the columns list,
        @param order: an expression to use in the ORDER BY clause.
        
        @rtype: list of dict
        """
        from_clause = self.schema + "." + self.name + " o LEFT JOIN " + self.schema + ".object_search_txt t ON o.objectid = t.objectid"
        return CFG.CX.query ( "SELECT o.objectid, t.txt as _astxt, o.objectmodification, {3} FROM {0} WHERE {1} ORDER BY {2}".format (from_clause, _filter, order, ",".join(select) )).dictresult()

    def recordObjectList(self, _filter="TRUE", select=['0'], order="objectid", recordObjectClass=None):
        """
        Same as recordList, but return a list of Record objects rather than dict objects.

        @type _filter: str
        @type select: str
        @type order: str
        
        @param _filter: an expression to use in the WHERE clause,
        @param select: an expression to append to the columns list,
        @param order: an expression to use in the ORDER BY clause.
        
        @rtype: list of Record
        """
        from ProvCon.dbui.orm import Record
        RecordClass = recordObjectClass or Record        
        rl = self.recordList(_filter, select, order)        
        li = []
        for r in rl:
            rec = RecordClass.EMPTY (self)
            rec.feedDataRow ( r )
            li.append (rec)
        return li
    
    def __iter__(self):        
        return iter(self.fields)            

    def __contains__(self, fname):
        """
        Check if a field of given name is in the table.

           >>> "objectid" in aTable
           True         
           
        @type fname: str
        @param fname: name of the field.
        @rtype: bool
        """        
        return fname in self.fields_hash
    
    def __getitem__(self, idx):
        """
        Get a field of a given name.
        
        @rtype: Field
        """
        if idx in self:
            return self.fields_hash[idx]
        return None

    def __repr__(self):
        return "<TABLE [" + self.schema + "." + self.name + "]>"
 
    