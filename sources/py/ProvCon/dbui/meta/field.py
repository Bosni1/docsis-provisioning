from errors import MetaDataError
from ProvCon.dbui.database import array_as_text, text_to_array

__revision__ = "$Revision$"

class Field(object):
    """
    Field objects represent column meta data and provide data-conversion services.

    Field objects are created when a connection is made to the database. Each Field
    object represents one column in the I{field_info} table. There should be no need
    for these objects to be created by the user elsewhere.    

    Data conversion SQL {<->} PYTHON is also handled by Field objects.    
    """    
    class IncompleteDefinition(MetaDataError): 
        """
        Raised when the Field constructor receives incomplete meta-data.
        """
        pass
    
            
    def __init__(self, name=None, type='text', size=-1, ndims=0, **kkw):
        try:            
            ndims = ndims or kkw.get('ndims', 0)
            self.name = name or kkw['name']
            self.type = type or kkw['type']
            self.size = size or kkw['size']
            self.lp = kkw.get ( "lp", -1 )
            self.isarray = kkw.get("isarray", ndims > 0)
            self.arraysize = kkw.get("arraysize", ndims )
            self.label = kkw.get("label", self.name)
            self.auto = kkw.get("auto", False)
            self.id = kkw.get("objectid", None)
            
            for k in kkw:
                if k not in self.__dict__: self.__dict__[k] = kkw[k]                        
            
            choices = text_to_array ( self.choices, 0 )
            self.choices = []
            for c in choices:
                if c.startswith("<["):
                    cv,cd = c[2:-2].split("::=")[:2]
                else:
                    cv,cd = c, c
                self.choices.append ( (cv, cd) )
                
            params = text_to_array ( self.editor_class_params, 0 ) or []            
            params = map ( lambda x: tuple(x.split("::=")), params )
            self.editor_class_params = {}
            for (pname, pvalue) in params:
                self.editor_class_params[pname] = pvalue
        except KeyError, e:
            kwname, = e.args
            raise Field.IncompleteDefinition ( "missing: '%s' in field definition." % kwname )
    
    def __repr__(self):
        return "{0} : {1}".format (self.name, self.type)

    
    def val_sql2py(self, sqlval):
        """
        Convert the value returned by postgres into a python variable.
        
        @type sqlval: str
        @param sqlval: value returned from a SELECT 
        
        @rtype: object
        """
        if self.isarray:
            return text_to_array (sqlval, self.arraysize-1)
        if self.type == 'bit': 
            if sqlval == '1': return True
            elif sqlval == '0': return False
            else: return None
        return sqlval
    
    def val_py2sql(self, pyval):
        """
        Convert a python variable into something we can insert into an pgSQL statement.
        
        @type pyval: object
        @param pyval: object represnting column value to be inserted .
        
        @rtype: str
        """        
        if pyval is None:
            return None
        elif self.isarray:
            return array_as_text (pyval)
        elif self.type == "bit":
            if pyval: return 1
            else: return 0
        elif isinstance(pyval, (str, unicode)):
            try:
                return pyval.encode ( 'utf-8')
            except UnicodeDecodeError:
                return pyval.decode ( 'utf-8' ).encode ( 'utf-8' )                
        else:
            return str(pyval)
    
    def val_py2txt(self, pyval):
        """
        Convert a python variable to text that can be displayed in an input widget.
        @type pyval: object
        @param pyval: object represnting column value to be inserted .
        
        @rtype: str
        """
        if self.isarray:
            return "array:" + array_as_text(pyval)
        if pyval is None:
            return ''
        elif isinstance(pyval, unicode):
            return pyval
        elif isinstance(pyval, str):
            return pyval.decode('utf-8')
        else:
            return str(pyval)
    
    def val_txt2py(self, txtval):
        """
        Convert text to a python variable.
        
        @type txtval: str
        @param txtval: text representation of column value
        
        @rtype: object
        """
        if self.isarray:
            return text_to_array ( txtval[6:], self.arraysize-1 )
        return txtval
    
    def encode(self, value):
        raise DeprecationWarning
    
    def decode(self, value):
        raise DeprecationWarning
    
    def isSpecial(self):
        """
        Check if the column is I{special}, meaning it holds object meta-data. 
        All columns inherited from the I{object} table are considered special.
        """
        from ProvCon.dbui.meta import Table
        return self.name in Table.__special_columns__
    

class VirtualField(object):
    """
    VirtualFields are fields used in gui forms, which do not have a corresponding column
    in the edited table.
    
    VirtualFields may have complex logic embedded into them, like foreign-key editing,
    displaying complex information about current record etc.
    """
    def __init__(self, name, **kw):
        self.name = name
        self.label = kw.get ( "label", self.name )
        
