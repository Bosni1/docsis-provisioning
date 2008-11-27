
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