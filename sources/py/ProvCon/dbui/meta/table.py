from ProvCon.dbui.database import CFG
import contextlib

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
    
    def fieldCount(self):
        return len ( filter (lambda f: not f.is_special(), self.fields ) )
    
    def addField(self, field):        
        if field.lp < 0: field.lp = len(self.fields)
        self.fields.append (field)        
        self.fields_hash[field.name] = field
        field.table = self
        self.fields.sort ( lambda x, y: x.lp - y.lp )
        
    def recordCount(self):
        return CFG.CX.query ( "SELECT count(*) as recordCount FROM {0}.{1} WHERE objectscope={2}".format(
            CFG.DB.SCHEMA, self.name, CFG.RT.DATASCOPE )).dictresult()[0]['recordCount']
                              
    def recordList(self, _filter="TRUE", select=['0'], order="objectid"):
        from_clause = self.schema + "." + self.name + " o LEFT JOIN " + self.schema + ".object_search_txt t ON o.objectid = t.objectid"
        return CFG.CX.query ( "SELECT o.objectid, t.txt as _astxt, o.objectmodification, {3} FROM {0} WHERE {1} ORDER BY {2}".format (from_clause, _filter, order, ",".join(select) )).dictresult()

    def recordObjectList(self, _filter="TRUE", select=['0'], order="objectid"):
        from ProvCon.dbui.orm import Record
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

def find_method_for_superclass(obj, prefix, record, default):
    table = record._table
    while table is not None:
        try:
            return getattr(obj, prefix + "_" + table.name)
        except AttributeError:
            table = table.superclass
    return default    
    