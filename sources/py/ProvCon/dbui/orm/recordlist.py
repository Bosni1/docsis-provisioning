
class RecordList(list):
    def __init__(self, table, _filter="TRUE", select=['0'], order="objectid", **kkw):
        list.__init__(self)
        self.table = table
        self.filter = _filter
        self.select = select
        self.order = order
        self.filterfunc = kkw.get("filterfunc", lambda r: True)
        self.hash_id = {}
    
    def reload(self):
        list.__init__(self)
        self += filter(self.filterfunc, self.table.recordObjectList (self.filter, self.select, self.order))
        self.hash_id.clear()
        for r in self: self.hash_id[r.objectid] = r
        return self
    
    def getid(self, objectid):
        return self.hash_id[objectid]


    