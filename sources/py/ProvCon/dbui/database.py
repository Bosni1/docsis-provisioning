import contextlib
import cStringIO
import pg, re
import exceptions

class CFG:
    """
    Static class containing application settings.
    """
    class DB:
        """
        Database back-end connection settings.
	"""
        @classmethod
        def initialize(cls):
            if cls.__is_initialized: return            
            from app import APP
            if APP.isFrontEnd:
                cls.HOST = APP.FE.DATABASE.host
                cls.PORT = APP.FE.DATABASE.port
                cls.DBNAME = APP.FE.DATABASE.dbname
                cls.ROLE = None
                cls.PASS = None
                cls.SCHEMA = APP.FE.DATABASE.schema
            elif APP.isBackEnd:
                cls.HOST = APP.BE.DATABASE.host
                cls.PORT = APP.BE.DATABASE.port
                cls.DBNAME = APP.BE.DATABASE.dbname
                cls.ROLE = None
                cls.PASS = None
                cls.SCHEMA = APP.BE.DATABASE.schema

            cls.__is_initialized = True
            
        HOST = None
        PORT = None
        DBNAME = None
        ROLE = None
        PASS = None
        SCHEMA = None
        __is_initialized = False
        
    class RT:
        @classmethod
        def initialize(cls):
            from app import APP
            if APP.isFrontEnd:
                cls.DATASCOPE = APP.FE.DATABASE.scope
            elif APP.isBackEnd:
                cls.DATASCOPE = APP.BE.DATABASE.scope
        DATASCOPE = None
        
    class tCX(pg.DB):        
        """    
        Besides being a PostgreSQL connection object, this class builds the ER
        structures used by forms, records, reference editors etc.
        
        Ideally it should only be instatiated once, the constructor attempts to
        ensure that it is so. The CFG.CX static variable should hold an active
        connection at all times.        
        """
        instanceCount = 0
        instance = None
        @staticmethod
        def reconnect():
            CFG.CX = CFG.tCX()
            
        def __init__(self):
            from meta import Table, Field
            pg.DB.__init__(self, dbname=CFG.DB.DBNAME, user=CFG.DB.ROLE, host=CFG.DB.HOST)            
            #Attempt to make sure this class is a singleton.
            CFG.tCX.instanceCount += 1
            print "tCX init [%d]" % self.instanceCount
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
                        idmap[t.objectid].reference_child.append ( (t, f) )
                        idmap[t.objectid].reference_child_hash[(t.name, f.name)] = (t,f)
                    if f.arrayof:
                        f.arrayof = idmap[f.arrayof]               
            #import many-to-many relationships
            mtm_info = self.query ( "SELECT * FROM ONLY {0}.mtm_relationship".format(CFG.DB.SCHEMA) ).dictresult()
            for mtm in mtm_info:
                table1 = Table.Get ( mtm['table_1'] )
                table2 = Table.Get ( mtm['table_2'] )
                
                table1.mtm_relationships[ mtm['relationship_name'] ] = ( 
                    mtm['table_1_handle'], mtm['mtm_table_name'], table2 )
                table1.mtm_relationships[ mtm['relationship_name'] ] = ( 
                    mtm['table_2_handle'], mtm['mtm_table_name'], table1 )
                
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

        CX = None

RaiseDBException = lambda *a: a

def array_as_text(arr):
    """
    Convert a python list to a text representation of a postgres array.
    
    @type arr: list
    @param arr: the python list to be converted
    
    @rtype: string
    @return: postgres array
    
    """
    if isinstance(arr, list):
        return "{" + ",".join(map(array_as_text, arr)) + "}"
    else:
        if arr is None: return ''
        else: return str(arr)

def text_to_array(text, depth):
    """
    Parse a text representation of a postgres array into a python list.
    
    @type text: str
    @param text: the postgres array 
    @type depth: int
    @param depth: depth of the array
    
    @rtype: list    
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
                if curitem.startswith('"') and curitem.endswith('"'):
                    curitem = curitem[1:-1]

                content.append ( curitem )
                if len(content) == 1 and curitem == '':
                    yield []
                else:                
                    yield content
                curitem = ''
                content = []      
                continue

            if char == ',' and prev != '\\' and bracestate == 1:                
                if curitem.startswith('"') and curitem.endswith('"'):
                    curitem = curitem[1:-1]
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


def StartupDatabaseConnection():    
    """
    Read configuration files, and connect to the database backend.
    """
    CFG.DB.initialize()
    CFG.RT.initialize()
    CFG.CX = CFG.tCX.instance or CFG.tCX()
    def sql_debugger ( qry ):
        import traceback, os.path
        st = traceback.extract_stack(limit=5)
        fname1, lineno1, fn1, code = st[-5]
        fname, lineno, fn, code = st[-4]
        print os.path.basename(fname1) + "/" + fn1 + (" >> {0} line {1} ({3}) SQL: {2}".format(os.path.basename(fname), lineno, qry, fn))
    CFG.CX.debug = sql_debugger
    #CFG.CX.debug = 
    
Init = StartupDatabaseConnection

