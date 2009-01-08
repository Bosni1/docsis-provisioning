from errors import MetaDataError
from ProvCon.dbui.database import array_as_text, text_to_array

__revision__ = "$Revision$"

class Field(object):
    """ ==Field==
    Field objects hold meta data about columns in the database.
    They also provide data-conversion services.
    A Field object is created from a row of the 'field_info' table.
    """    
    class IncompleteDefinition(MetaDataError): 
        """raised when the Field constructor receives incomplete meta-data"""
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
        """convert the value returned by pg into a python variable"""
        if self.isarray:
            return text_to_array (sqlval, self.arraysize-1)
        if self.type == 'bit': 
            if sqlval == '1': return True
            elif sqlval == '0': return False
            else: return None
        return sqlval
    
    def val_py2sql(self, pyval):
        """convert a python variable into something we can insert into an pgSQL statement"""        
        if pyval is None:
            return None
        elif self.isarray:
            return array_as_text (pyval)
        elif self.type == "bit":
            if pyval: return 1
            else: return 0
        elif isinstance(pyval, (str, unicode) ):
            return str(pyval.encode('utf-8'))
        else:
            return str(pyval)
    
    def val_py2txt(self, pyval):
        if self.isarray:
            return "array:" + array_as_text(pyval)
        if pyval is None:
            return ''
        elif isinstance(pyval, str):
            return pyval.decode('utf-8')
        else:
            return str(pyval)
    
    def val_txt2py(self, txtval):
        if self.isarray:
            return text_to_array ( txtval[6:], self.arraysize-1 )
        return txtval
    
    def encode(self, value):
        raise DeprecationWarning
    
    def decode(self, value):
        raise DeprecationWarning
    
    def is_special(self):
        from ProvCon.dbui.meta import Table
        return self.name in Table.__special_columns__
    
