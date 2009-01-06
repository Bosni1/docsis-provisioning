from ProvCon.dbui.orm import Record

class ObjectFlags(object):
    def __init__(self, _object):
        self._object = _object
        self._flags = {}
        
    def update(self):
        self._flags = {}
        for flagRecord in self._object.CHILDREN (self._object.objectid, "object_flag", "refobjectid"):
            self._flags[flagRecord.flagname.upper()] = flagRecord.objectid

    def _flag_isset(self, flagname):
        return flagname.upper() in self._flags
    def _flag_del(self, flagname):
        if self._flag_isset(flagname):
            oldFlag = Record.ID ( self._flags[flagname.upper()] )
            oldFlag.delete()
            self.update()
    
    def _flag_add(self, flagname):
        if not self._flag_isset(flagname):
            newFlag = Record.EMPTY ( "object_flag" )
            newFlag.refobjectid = self._object.objectid
            newFlag.flagname = flagname.upper()
            newFlag.write()
            self.update()
            
    def __getattr__(self, attrname):
        if attrname.startswith ( "_" ): return self.__dict__[attrname]
        return self._flag_isset(attrname)
    
    def __setattr__(self, attrname, attrval):
        if attrname.startswith("_"):
            self.__dict__[attrname] = attrval
        elif attrval:
            self._flag_add(attrname)
        else:
            self._flag_del(attrname)
            
    def __delattr__(self, attrname):
        self.__setattr__(attrname, False)
            


class ObjectParams(object):
    def __init__(self, _object):
        self._object = _object
        self._params = {}
        self._params_id = {}

    def update(self):
        self._params = {}
        self._param_id = {}
        for paramRecord in self._object.CHILDREN (self._object.objectid, "object_parameter", "refobjectid"):
            self._params[paramRecord.parametername.upper()] = paramRecord.content
            self._params_id[paramRecord.parametername.upper()] = paramRecord.objectid

    def _param_get(self, paramname):
        return self._params.get( paramname.upper(), None )
    def _param_set(self, paramname, paramval):
        if self._param_get(paramname):
            if paramval is None: 
                self._param_del (paramname)
            else:
                oldParam = Record.ID ( self._params_id[paramname.upper()] )
                oldParam.content = paramval
                oldParam.write()
                self.update()
        elif paramval is not None:
            newParam = Record.EMPTY ( "object_parameter" )
            newParam.refobjectid = self._object.objectid
            newParam.parametername = paramname.upper()
            newParam.content = paramval
            newParam.write()
            self.update()            
    def _param_del(self, paramname):
        if self._param_get(paramname):
            oldParam = Record.ID ( self._params_id[paramname.upper()] )
            oldParam.delete()
            self.update()
        
    def __getattr__(self, attrname):
        if attrname.startswith ( "_" ): return self.__dict__[attrname]
        return self._param_get(attrname)
    
    def __setattr__(self, attrname, attrval):
        if attrname.startswith("_"):
            self.__dict__[attrname] = attrval
        else:
            self._param_set(attrname, attrval)
            
    def __delattr__(self, attrname):
        if attrname.startswith ( "_" ): del self.__dict__[attrname]
        else: self.__setattr__(attrname, None)
        
        
class rObject (Record):
    def __init__(self, table="object", **kkw):
        Record.__init__(self, **kkw)
        self.setTable ( table )
        self._new = True
        self._flags = None
        self._params = None
        self._events = None
        self._notes = None
        
    def getFlags(self):
        if not self._flags: 
            self._flags = ObjectFlags(self)        
            self._flags.update()            
        return self._flags
    FLAGS = property (getFlags)
    
    def getParams(self):
        if not self._params: 
            self._params = ObjectParams(self)        
            self._params.update()            
        return self._params
    PARAM = property (getParams)
     