
import pg
from app import APP

class DatabaseConnection(pg.DB):
    instanceCount = 0
    instance = None
    
    @staticmethod
    def reconnect():
        CFG.CX = CFG.tCX()
            
    def __init__(self, **kwargs):
        from meta import Table, Field
        pg.DB.__init__(self, **kwargs)            
        #Attempt to make sure this class is a singleton.
        CFG.tCX.instanceCount += 1
        APP.log("tCX init [%d]" % self.instanceCount)
        self.schemaname = CFG.DB.SCHEMA
        idmap = {}
        tableinfo = self.query ( "SELECT * FROM ONLY {0}.table_info".format(CFG.DB.SCHEMA) ).dictresult()
        for ti in tableinfo:
            with Table.New ( ti['name'], **ti ) as t:
                columninfo = self.query ( "SELECT * FROM ONLY {0}.field_info WHERE classid = {objectid}".format(CFG.DB.SCHEMA, **ti)).dictresult()
                for ci in columninfo:                        
                    t.addField ( Field (size=ci['length'], **ci) )
                idmap[t.objectid] = t
                t.recordlisttoolbox = text_to_array ( t.recordlisttoolbox, 0 )
                t.recordlistpopup = text_to_array ( t.recordlistpopup, 0 )
    
        #import foreign key relationships
        for t in Table.__all_tables__.values():
            if t.superclass: t.superclass = idmap[t.superclass]
            else: t.superclass = None
            for f in t.fields:
                #For columns that reference a table_info row, replace the appropriate
                #values with actual, python-object references
                if f.reference: 
                    f.reference = idmap[f.reference]
                    #fill the table's children list
                    f.reference.reference_child.append ( (t, f) )
                    f.reference.reference_child_hash[t.name + "_" + f.name] = (t,f)
                if f.arrayof:
                    f.arrayof = idmap[f.arrayof]               
        #import many-to-many relationships
        mtm_info = self.query ( "SELECT * FROM ONLY {0}.mtm_relationship".format(CFG.DB.SCHEMA) ).dictresult()
        for mtm in mtm_info:
            table1 = Table.Get ( mtm['table_1'] )
            table2 = Table.Get ( mtm['table_2'] )
            
            table1.mtm_relationships[ mtm['table_1_handle'] ] = ( 
                mtm['relationship_name'], mtm['mtm_table_name'], "refobjectid1", "refobjectid2", table2 )
            table2.mtm_relationships[ mtm['table_2_handle'] ] = ( 
                mtm['relationship_name'], mtm['mtm_table_name'], "refobjectid2", "refobjectid1", table1 )
            
        self.instance = self
        
    def delete(self, cl, a):
        """Delete an existing row in a database table.
    
        This method deletes the row from a table.
        It deletes based on the objectid	    
        """
        qcl = pg._join_parts(self._split_schema(cl)) # build qualified name	    
        
        q = 'DELETE FROM %s WHERE objectid=%s' % (qcl, a['objectid'] )
        self._do_debug(q)
        self.db.query(q)
