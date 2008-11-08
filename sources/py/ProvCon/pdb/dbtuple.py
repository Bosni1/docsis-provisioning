from cStringIO import StringIO
from connection import Abstract, ProvisioningDatabase
from re import match as regmatch

class tablesignature(object):
    class field(object):
        def __init__(self, **params):
            for p in params:
                self.__dict__[p] = params[p]
            if self.type.startswith("array:"):
                self.isarray = True
                self.type = self.type[6:]
            else:
                self.isarray = False
        
        def getdefault(self):
            return ""
        
        def tosql(self, v):
            if isinstance(v, list):
                return "{" + ",".join( v ) + "}"
            else:
                return v
            
        def _getarray(self, v):
            v = regmatch("\{(.*)\}", v).group(1)
            return v.split(",")
        
        def fromsql(self, v):            
            if self.isarray and v:                
                r = [v]
                i = self.ndims
                while i>0:
                    r = map ( self._getarray, r )
                    i -= 1
                return r[0]
            return v
        
        def __repr__(self):
            return "{0.name} : {0.type} ''{0.label}''".format ( self )
        
    def __init__(self, tblname, tblfields, **options):
        self.tblname = tblname
        self.tblfields = {}
        for fname in tblfields:
            self.tblfields[fname] = self.field ( ** tblfields[fname] )
            
        for optname in options:            
            self.__dict__[optname] = options[optname]
    
    def isfield(self, name):
        return name in self.tblfields
    
    def setcolumnvalue (self, tupleobj, colname, colval):
        assert isinstance(tupleobj, dbtuple)
        tupleobj.__setattr__ ( "v___!" + colname, colval )

    def recordrepr(self, tupleobj):
        return self.pprint_expression % tupleobj.__dict__
        
    def free(self, tupleobj):
        for f in self.tblfields:
            del tupleobj.__dict__[f.name]
        tupleobj._isresolved = False
        tupleobj._isread = False
        tupleobj._ismodified = False
        tupleobj._modifiedcols.clear()

    def fill(self, tupleobj):        
        for f in self.tblfields.values():            
            tupleobj.__dict__[f.name]  = f.getdefault()
        tupleobj._isresolved = True
        tupleobj._isread = False
        tupleobj._ismodified = False
        tupleobj._modifiedcols.clear()

    def write(self, tupleobj):
        assert isinstance(tupleobj, dbtuple)

        mod = map (lambda x: (x, self.tblfields[x].tosql(tupleobj.__dict__[x])), tupleobj._modifiedcols )
        modifications = {}
        modifications.update ( mod )
        modifications['objectscope'] = dbtuple.__objectscope__
        
        if tupleobj._ismodified is True:
            if tupleobj._objectid:
                if tupleobj._isread is not True:
                    raise Exception("cannot write: row not in memory" )
                else:
                    modifications['objectid'] = tupleobj._objectid
                    dbtuple.DB.update ( self.tblname, modifications )
                    tupleobj.read()
            else:                                
                tupleobj._objectid = dbtuple.DB.insert (  self.tblname, modifications )
                tupleobj.read()             
                
        elif not tupleobj._ismodified:
            if tupleobj._objectid:
                pass
            elif tupleobj._isresolved:
                tupleobj._objectid = dbtuple.DB.insert ( self.tblname, {} )
                tupleobj.read()
    
    def read(self, tupleobj):        
        assert isinstance(tupleobj, dbtuple)
        if tupleobj._objectid:
            row = dbtuple.DB.get ( self.tblname, { 'objectid' : tupleobj._objectid } )            
            for cn in row:
                tupleobj.__dict__[cn] = self.tblfields[cn].fromsql(row[cn])
            tupleobj._isread = True
            tupleobj._ismodified = False
            tupleobj._modifiedcols.clear()
    
    def __iter__(self): 
        fs = self.tblfields.values()
        fs.sort ( lambda x, y: x.lp - y.lp )
        return iter(fs)
    
    def __repr__(self):
        rpr = StringIO()
        rpr.write ( "Table: `%s`\n" % self.tblname )
        for f in self.tblfields.values():
            rpr.write ( "\t" + repr(f) + "\n" )
        return rpr.getvalue()
        
class dbtuple(object):
    class db(ProvisioningDatabase):        
        def __init__(self, **kkw):
            ProvisioningDatabase.__init__(self, **kkw)
            
        def objectheader(self, objectid):
            return self.get ( "pv.object", { 'objectid' : objectid, 'objectscope' : dbtuple.__objectscope__  } )
    
    __objectscope__ = 0
    __signatures__ = {}
    DB = db()
    
    def __init__(self, objectid = None, resolve=True, table = None, read=False):
        self._isresolved = False        
        self._isread = False
        self._objectid = objectid
        self._ismodified = False
        self._modifiedcols = set()
        
        if table: self.settype (table)        
        if resolve: self.resolve()
        if read: self.read()
        
        
    def __setattr__(self, attrname, attrval):
        if attrname.startswith("_"):
            return object.__setattr__(self, attrname, attrval)
        if self._signature:
            if attrname.startswith ( "v___!" ):
                attrname = attrname[5:]
                if self._signature.isfield ( attrname):
                    self._ismodified = True
                    self._modifiedcols.add (attrname)
                    return object.__setattr__(self, attrname, attrval)
            elif attrname == "objectid":
                self._objectid = attrval
                self.resolve()
            elif self._signature.isfield (attrname):                
                self._signature.setcolumnvalue (self, attrname, attrval)
    def __getitem__(self, attrname):
        return self.__dict__[attrname]
    
    def settype(self, tablename):
        if self._isresolved:
            if tablename == self._signature.name: return
            self.free()
        else:            
            self._signature = self.__signatures__.get ( tablename, None )
            self._objectid = None
        self._isresolved = False
        
    def resolve(self):
        if self._objectid:
            if self._isresolved: self.free()
            header = self.DB.objectheader(self._objectid)
            if header:
                self._signature = self.__signatures__["pv." + header["objecttype"]]
                self.fill()
        elif self._signature and not self._isresolved:
            self.fill()

    def flag(self, columnname):
        self._ismodified = True
        self._modifiedcols.add (columnname)
            
    def free(self):
        self._signature.free(self)
        
    def fill(self):        
        self._signature.fill(self)
        
    def write(self):
        self._signature.write(self)        

    def read(self):
        self._signature.read(self)
    
    def __repr__(self):
        rpr = StringIO()
        if self._isresolved:
            rpr.write ( "<{0}>".format ( self._signature.name ) )
            if self._objectid:
                rpr.write ( " #{0}".format ( self._objectid ) )
            else:
                rpr.write ( " NEW" )
            rpr.write ( self._signature.recordrepr ( self ) )
        elif self._objectid:
            rpr.write ( "<__obj__> #{0}".format (self._objectid ) )
        else:
            rpr.write  ("<void db object>")
        return rpr.getvalue()
    
    def tabular(self, header=False, system=False):
        rpr = StringIO()
        fs = self._signature.tblfields.values()
        fs.sort ( lambda x, y: x.lp - y.lp )
        for f in fs:
            if f.name in ["objectscope", "objectcreation", "objectdeletion", "objecttype", "objecttypeid"] and not header: continue
            if f.name in ["xmax", "xmin", "cmax", "cmin", "ctid", "tableoid"] and not system: continue            
            rpr.write ( "{0:24} := {1}\n".format ( f.label, self.__dict__[f.name] ) )
        return rpr.getvalue()
    tabularrepr = tabular
    
A = Abstract()
for t in A: dbtuple.__signatures__.update ( [( t[0] + "." + t[1], tablesignature (  t[0] + "." + t[1], A[t]['fields'], **A[t] ),)] )

