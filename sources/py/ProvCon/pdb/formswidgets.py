#!/bin/env python
import Tix
from Tkconstants import *
from orm import *
from forms import *

class GenericForm(object):
    def __init__(self, parent, form, *args, **kwargs):
        self.parent = parent
        self.toplevel = Tix.Frame (parent)
        scrolled = Tix.ScrolledHList (self.toplevel)
        self.hlist = scrolled.subwidget('hlist')
        #self.hlist.configure ( columns
        self.pack = self.toplevel.pack
        self.place = self.toplevel.place
        
        
        
        
    

class MetadataEditorApp:
    resource_dir = '/home/kuba/src/docsis-resources/'
    def __init__(self):
        self._root = Tix.Tk()
        
        self.rootwindow = Tix.Frame(self._root)

        wm = self._root.winfo_toplevel()        
        wm.title ( "Provisioning meta-data editor" )
        wm.geometry ( "1024x768+10+10" )

        self.rootwindow.propagate(0)
        self.rootwindow.pack(expand=1, fill=BOTH)
        
                
        self.table_list_frame = Tix.LabelFrame(self.rootwindow, label="Table list")
        self.table_list_frame.place ( relx=0, rely=0, relwidth=0.5, relheight=0.5)
        self.table_list_frame.propagate(0)
        
        scrolled = Tix.ScrolledTList ( self.table_list_frame, scrollbars='auto y' )
        self.table_list = scrolled.subwidget('tlist')
        self.table_list.configure(selectmode="single",
                                  bg='white', selectbackground="blue",
                                  selectforeground="white",                                      
                                  orient='horizontal', command=self.table_change_handler)
        scrolled.pack (expand=1, fill=BOTH, padx=7, pady=20)

        self.table_icon = Tix.Image ('bitmap','table', file= (self.resource_dir + 'bitmaps/justify.xbm') ) 
        self.table_items = {}
        for idx, t in enumerate(Table.__all_tables__):
            self.table_items[idx] = Table.Get(t)
            self.table_list.insert (END, itemtype="imagetext", text=t, image=self.table_icon)
            
        
        self.table_properties_frame = Tix.LabelFrame (self.rootwindow, label="Table properties" )
        self.table_properties_frame.place (relx=0.50, rely=0, relwidth=0.5, relheight=0.5)

        self.table_properties = GenericForm (self.table_properties_frame, 0, 0)
        
        
        self.field_list_frame = Tix.LabelFrame(self.rootwindow, label="Fields")
        self.field_list_frame.place ( relx=0, rely=0.51, relwidth=0.4, relheight=0.45)
        scrolled = Tix.ScrolledTList(self.field_list_frame, scrollbars='y')
        self.field_list = scrolled.subwidget('tlist')
        self.field_list.configure (selectmode="single",
                                   bg='white', selectbackground="blue",
                                   selectforeground="white", orient='vertical',                                   
                                   command=self.field_change_handler )
        self.field_items = {}
        scrolled.pack (expand=1, fill=BOTH, padx=7, pady=20)

        self.field_properties_frame = Tix.LabelFrame (self.rootwindow, label="Field properties" )
        self.field_properties_frame.place (relx=0.40, rely=0.51, relwidth=0.6, relheight=0.45)
        
        #a = Tix.TList()        
        self.normal_field_style = Tix.DisplayStyle ( Tix.IMAGETEXT, refwindow=self.field_list, font = ("Helvetica", 11, "bold" ), foreground="black", bg='white' )
        self.special_field_style = Tix.DisplayStyle ( Tix.IMAGETEXT, refwindow=self.field_list, font = ("Helvetica", 11, "italic" ), foreground="grey", bg='white' )        
        self._root.mainloop()        

        
        
    def table_change_handler(self, idx):
        table = self.table_items[int(idx)] 
        for m in self.field_items:
            self.field_list.delete(m)
        self.field_items.clear()
        self.field_list_frame.configure ( label = table.name + " fields" )
        for idx, f in enumerate(table):
            if f.name in Table.__special_columns__: style = self.special_field_style
            else: style = self.normal_field_style
            self.field_list.insert (END, itemtype="imagetext", text=str(f),style=style) 
            self.field_items[idx] = f
    
    def field_change_handler(self, idx):
        field = self.field_items[int(idx)]
        self.field_properties_frame.configure ( label = field.path )
        
        
MetadataEditorApp()
