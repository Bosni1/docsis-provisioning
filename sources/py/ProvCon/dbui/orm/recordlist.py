
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
        self += self.table.recordObjectList (self._filter, self.select, self.order)
        self.hash_id.clear()
        for r in self: self.hash_id[r.objectid] = r
        return self
    
    def getid(self, objectid):
        return self.hash_id[objectid]