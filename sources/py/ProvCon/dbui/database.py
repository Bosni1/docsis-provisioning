import contextlib
import cStringIO
import pg, re
import exceptions
from config import config

class CFG:
    """not really a class, just a nice-looking storage for application settings"""
    class DB:
        HOST = config.get ( "DATABASE", "host" )
        PORT = config.get ( "DATABASE", "port" )
        DBNAME = config.get ( "DATABASE", "dbname" )
        ROLE = None
        PASS = None
        SCHEMA = config.get ( "DATABASE", "schema" )        
    class RT:
        DATASCOPE = config.get ( "DATABASE", "scope" )        
    class tCX(pg.DB):        
        """==tCX==
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
            self.instance = self
        
    CX = None

def array_as_text(arr):
    """convert a python list to a textual representation of a postgres array"""
    if isinstance(arr, list):
        return "{" + ",".join(map(array_as_text, arr)) + "}"
    else:
        if arr is None: return ''
        else: return str(arr)

def text_to_array(text, depth):
    """parse a textual postgres array into a python list
    depth - the number of dimensions the array has
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
                content.append ( curitem )
                if len(content) == 1 and curitem == '':
                    yield []
                else:                
                    yield content
                curitem = ''
                content = []      
                continue
            
            if char == ',' and prev != '\\' and bracestate == 1:                
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
    print "DB STARTUP"
    CFG.CX = CFG.tCX.instance or CFG.tCX()


StartupDatabaseConnection()