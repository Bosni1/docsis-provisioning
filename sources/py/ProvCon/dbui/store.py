##$Id$
import orm, meta, di
from functools import partial

def basic_store_initializer(tablename, store, select=['*'], order='objectid',_filter='TRUE',recordclass=di.rObject):
    if tablename in store:
        self[tablename].reload()
    else:
        print "DataStore.{0} initialization.".format (tablename)
        store.__recordlists__[tablename] = orm.RecordList ( meta.Table.Get (tablename),
                                                           select=select, 
                                                           order=order,
                                                           _filter=_filter,
                                                           recordclass=recordclass).reload()
    return store[tablename]
        
class Store:
    def __init__(self):
        self.__recordlists__ = {}
    
    init__subscriber = partial(basic_store_initializer, "subscriber",  order="name" )
    init__service = partial(basic_store_initializer, "service",  order="ownerid" )
    init__city = partial(basic_store_initializer, "city",  order="name" )    
    init__street = partial(basic_store_initializer, "street", order="cityid, name" )
    init__building = partial(basic_store_initializer, "building", order="streetid, number" )
    init__location = partial(basic_store_initializer, "location", order="buildingid, number" )
    init__table_info = partial(basic_store_initializer, "table_info", order="name" )
    init__field_info = partial(basic_store_initializer, "field_info", order="classid, lp" )
    
    def __getattr__(self, attrname):
        if attrname in self.__dict__:
            return self.__dict__[attrname]
        elif attrname in self.__recordlists__:
            return self.__recordlists__[attrname]
        else:
            try:
                initializer = getattr(Store, "init__" + attrname)                
            except AttributeError:
                raise AttributeError("DataStore not defined '{0}'".format(attrname) )
            return initializer(store=self)
        
    def __getitem__(self, key):
        return self.__getattr__ ( key )
     
    def __contains__(self, key):
        return key in self.__recordlists__