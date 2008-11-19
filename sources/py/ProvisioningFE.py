#!/bin/env python
import Tix
from Tkconstants import *
from gettext import gettext as _
from ProvCon.dbui import *

class MetadataEditorApp:    
    resource_dir = '/home/kuba/src/docsis-resources/'
    def __init__(self):
        self._root = Tix.Tk()
        
        self.rootwindow = Tix.Frame(self._root)

        wm = self._root.winfo_toplevel()        
        wm.title ( "Provisioning meta-data editor" )
        wm.geometry ( "1024x768+10+10" )
        
        self.rootwindow.pack(expand=1, fill=BOTH)
        self.rootwindow.propagate(0)
                
        self.table_list_frame = Tix.LabelFrame(self.rootwindow, label="Table list")
        self.table_list_frame.place ( relx=0, rely=0, relwidth=0.5, relheight=0.5)
        self.table_list_frame.propagate(0)

        self.table_record_list = RecordListWidget(self.table_list_frame)        
        self.table_record_list.pack(expand=1, fill=BOTH, padx=10, pady=20)
        self.table_record_list.setObjectIDs ( Record.IDLIST ( "table_info", order=["name"] ) )        
        self.table_change_hook = self.table_record_list.register_event_hook ( "current_record_changed", self.table_changed )
            
        
        self.table_properties_frame = Tix.LabelFrame (self.rootwindow, label="Table properties" )
        self.table_properties_frame.place (relx=0.50, rely=0, relwidth=0.5, relheight=0.5)
        self.table_properties_frame.propagate(0)
        self.table_properties_form = Form ( Table.Get ( "table_info" ) )        
        self.table_properties = GenericFormEditor (self.table_properties_frame, 
                                                   self.table_properties_form,
                                                   disablefields = ["name", "schema"] )
        
        self.table_properties.pack(fill=BOTH, expand=1,padx=7, pady=20)
        
        self.field_list_frame = Tix.LabelFrame(self.rootwindow, label="Fields")
        self.field_list_frame.place ( relx=0, rely=0.51, relwidth=0.4, relheight=0.45)
        self.field_list_frame.propagate(0)
        
        self.field_record_list = RecordListWidget (self.field_list_frame, 
                                                   parentform=self.table_properties_form,
                                                   referencefield = "classid",
                                                   objecttype = "field_info",
                                                   filterfunc = lambda x: x.name not in Table.__special_columns__ )
        self.field_record_list.pack (expand=1, fill=BOTH, padx=10, pady=20)
        self.field_change_hook = self.field_record_list.register_event_hook ( "current_record_changed", self.field_change )
                    
        self.field_properties_frame = Tix.LabelFrame (self.rootwindow, label="Field properties" )
        self.field_properties_frame.place (relx=0.40, rely=0.51, relwidth=0.6, relheight=0.45)
        self.field_properties_frame.propagate(0)
        self.field_properties_form = Form ( Table.Get ( "field_info" ) )
        self.field_properties = GenericFormEditor (self.field_properties_frame,
                                                   self.field_properties_form ,
                                                   disablefields = [ "name", "type"],
                                                   excludefields = [ "path", "ndims" ]
                                                   )
        self.field_properties.pack (fill=BOTH, expand=1,padx=7, pady=20)
        
        self._root.mainloop()        
                        
    def table_changed(self,table_record,*args,**kwargs):
        table = Table.Get ( table_record.name )                
        self.table_properties_form.setid ( table.id )
        self.table_properties_frame.configure ( label = self.table_properties_form.current._astxt ) 
        
    def field_change(self, field_record,*args, **kwargs):
        self.field_properties_form.setid ( field_record.objectid )
        self.field_properties_frame.configure ( label = self.field_properties_form.current._astxt )        
                

MetadataEditorApp()
