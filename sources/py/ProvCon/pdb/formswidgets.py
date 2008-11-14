#!/bin/env python
import Tix
from Tkconstants import *
from orm import *
from forms import *
from gettext import gettext as _


class GenericFormEditor(object):    
    """ 
    ==GenericFormEditor==
    """
    __defaults__ = [ 
        ( "labelwidth", 20 ),
        ( "entrywidth", 40 ),
        ( "excludefields", []),
        ( "disablefields", []),
        ( "shownavigator", False),
        ( "showbuttons", True),
        ( "buttons", ["save", "reload", "new"] ),
    ]
    _button_label_ = {
        "save" : ( _("Save"), None),
        "reload" : ( _("Reload"), None),
        "new" : ( _("New"), None)
    }
    def __init__(self, parent, form, *args, **kwargs):
        for (attrname, defval) in self.__defaults__:
            self.__dict__[attrname] = kwargs.get ( attrname, defval )
            
        self.parent = parent
        self.toplevel = Tix.Frame (parent)
        scrolled = Tix.ScrolledHList (self.toplevel, options="hlist.columns 3")

        self.hlist = scrolled.subwidget('hlist')
        self.hlist.configure ( separator="/",
                               background="white", foreground="black",
                               selectbackground="white", selectforeground="black")
        
        self.pack = self.toplevel.pack
        self.place = self.toplevel.place
      
        scrolled.pack(side=TOP, fill=BOTH, expand=1)
        scrolled.propagate(0)
        
        if self.showbuttons:
            self.buttonbox = Tix.ButtonBox(self.toplevel, pady=0)
            for b in self.buttons: self.add_button(b)
            self.buttonbox.pack (side=BOTTOM, anchor=W )
        
        self.hlist.column_width(0, chars=1)
        self.hlist.column_width(1, chars=self.labelwidth)
        self.hlist.column_width(2, chars=self.entrywidth)
        
        self.form = form
        self.editor_widgets = {}
        style = Tix.DisplayStyle(Tix.WINDOW, refwindow=self.hlist)

        self.build_form()
        
    def build_form(self):
        for f in self.form.table:            
            if (f.name in Table.__special_columns__ 
                or f.name in self.excludefields): continue           
            self.hlist.add ( f.name, itemtype=Tix.TEXT, text="*" )
            self.set_label ( f.name, f.label )
            self.set_entry ( f.name, f )
            

    def set_label(self, form_element, label):
        self.hlist.item_create ( form_element, 1, itemtype=Tix.TEXT, text=label)

    def set_entry(self, form_element, field):
        entry = Tix.Entry (self.hlist, width=self.entrywidth)
        entry.__var = self.form.tkvars[form_element]
        entry.config ( textvariable = entry.__var )
        if form_element in self.disablefields: entry.config ( state='disabled' )
        self.editor_widgets[form_element] = entry
        self.hlist.item_create ( form_element, 2, itemtype=Tix.WINDOW, window=entry )
        
    def button_command(self, buttonname, *args):                
        if hasattr(self, "handle_button_" + buttonname):
            getattr(self, "handle_button_" + buttonname)(*args)
            
    def handle_button_save(self, *args):
        self.form.save()

    def handle_button_reload(self, *args):
        self.form.reload()
            
    def add_button(self, buttonname, **kwargs):
        self.buttonbox.add ( buttonname, text=buttonname, command=lambda *x: self.button_command(buttonname, *x) )
    
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
        self.table_properties_frame.propagate(0)
        self.table_properties_form = Form ( Table.Get ( "table_info" ) )
        self.table_properties = GenericFormEditor (self.table_properties_frame, 
                                                   self.table_properties_form,
                                                   disablefields = ["name", "schema"] )
        self.table_properties.pack(fill=BOTH, expand=1,padx=7, pady=20)
        
        self.field_list_frame = Tix.LabelFrame(self.rootwindow, label="Fields")
        self.field_list_frame.place ( relx=0, rely=0.51, relwidth=0.4, relheight=0.45)
        self.field_list_frame.propagate(0)
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
        self.field_properties_frame.propagate(0)
        self.field_properties_form = Form ( Table.Get ( "field_info" ) )
        self.field_properties = GenericFormEditor (self.field_properties_frame,
                                                   self.field_properties_form ,
                                                   disablefields = [ "name", "type"],
                                                   excludefields = [ "path", "ndims" ]
                                                   )
        self.field_properties.pack (fill=BOTH, expand=1,padx=7, pady=20)
        
        self.normal_field_style = Tix.DisplayStyle ( Tix.IMAGETEXT, refwindow=self.field_list, font = ("Helvetica", 11, "bold" ), foreground="black", bg='white' )
        self.special_field_style = Tix.DisplayStyle ( Tix.IMAGETEXT, refwindow=self.field_list, font = ("Helvetica", 11, "italic" ), foreground="grey", bg='white' )        
        self._root.mainloop()        
                
    def table_change_handler(self, idx):
        table = self.table_items[int(idx)] 
        for m in self.field_items:
            self.field_list.delete(m)
        self.field_items.clear()

        for idx, f in enumerate(table):
            if f.name in Table.__special_columns__: style = self.special_field_style
            else: style = self.normal_field_style
            self.field_list.insert (END, itemtype="imagetext", text=str(f),style=style) 
            self.field_items[idx] = f
        
        self.table_properties_form.setid ( table.id )
        self.table_properties_frame.configure ( label = self.table_properties_form.current._astxt ) 
        
        
    def field_change_handler(self, idx):
        field = self.field_items[int(idx)]
        self.field_properties_form.setid ( field.id )
        self.field_properties_frame.configure ( label = self.field_properties_form.current._astxt )
        
MetadataEditorApp()
