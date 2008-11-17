#!/bin/env python
import Tix
from Tkconstants import *
from orm import *
from forms import *
from gettext import gettext as _
from misc import *

class FieldEntry(object):
    
    def __init__(self, formeditor, parent, field, **kwargs):
        self.parent = parent
        self.formeditor = formeditor
        self.field = field
        self.form = self.formeditor.form
        self.variable = self.formeditor.form.tkvars[self.field.name]

    def disable(self):
        self.widget.config ( state='disabled' )
        
class TextEntry(FieldEntry):
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.widget = Tix.Entry (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 textvariable = self.variable)
        

class StaticEntry(FieldEntry):
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.widget = Tix.Label (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 textvariable = self.variable)    

class ReferenceEntry(FieldEntry):
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)    
        self.value_change = conditionalmethod(self.value_change)        
        self.variable.trace ( 'w', self.value_change )
    
    def value_change(self, *args):
        pass
    
    
class StaticReferenceEntry(ReferenceEntry):    
    def __init__(self, *args, **kwargs):
        ReferenceEntry.__init__(self, *args, **kwargs)        
        self.display_variable = Tix.StringVar()
        self.widget = Tix.Label (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 textvariable = self.display_variable)
        

    def value_change(self, *args):
        self.display_variable.set ( getattr(self.formeditor.form.current, self.field.name + "_REF") )

class ComboReferenceEntry(ReferenceEntry):
    def __init__(self, *args, **kwargs):
        ReferenceEntry.__init__(self, *args, **kwargs)                
        self.cmb_command = conditionalmethod(self.cmb_command)

        reftable = self.field.reference        
        self.records = RecordList(reftable)
        self.records.reload()
        
        self.display_variable = Tix.StringVar()
        
        self.widget = Tix.ComboBox (self.parent, 
                                    editable=False, dropdown=True,
                                    options = "label.width 0 entry.width " + str(self.formeditor.entrywidth),                                     
                                    variable = self.display_variable,
                                    command=self.cmb_command)        
                                                                    
        self.listbox = self.widget.subwidget('slistbox').subwidget('listbox')
        for r in self.records:
            self.widget.insert (Tix.END, r._astxt)
        self.widget.insert (Tix.END, "<no object>" )
        
        self.current = None        
    
    def cmb_command(self, *args):  
        
        #Was the call initiated by the ComboBox constructor?
        if not hasattr(self, 'listbox'): return        
        try:
            self.value_change.freeze()        
            idx, = self.listbox.curselection()
            self.current = self.records[int(idx)]
            self.variable.set (self.current.objectid)
        except IndexError:
            self.current = None
            self.display_variable.set ( "<error> out of bounds" )
        finally:
            self.value_change.thaw()
    
    def value_change(self, *args):                
        """Handle a change in the field value initiated outside of 
        this editor"""                
        try:
            self.cmb_command.freeze()
            self.current = None
            self.display_variable.set ( "")
            self.current = self.records.getid(int(self.variable.get()))
            self.display_variable.set ( self.current._astxt )
        except ValueError:
            pass            
        except KeyError:
            pass
        finally:
            self.cmb_command.thaw()
        
        
        



class ArrayEntry(FieldEntry):
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.branch = kwargs.get ( "branch", None )
class BooleanEntry(FieldEntry):
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.display_variable = Tix.StringVar()        
        self.widget = Tix.Checkbutton ( self.parent, textvariable = self.display_variable, 
                                        variable = self.variable )
        self.variable.trace ( 'w', self.value_change )
    
    def value_change(self, *args):
        if self.variable.get() == '1':
            self.display_variable.set (_("YES"))
        else:
            self.display_variable.set (_("NO"))
    
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
        self.create_toplevel()
        self.pack = self.toplevel.pack
        self.place = self.toplevel.place

        
        self.form = form
        self.editor_widgets = {}

        self.create_form_container()        
        self.build_form()
    
    def create_toplevel(self):
        self.toplevel = Tix.Frame (self.parent)
        

    def create_form_container(self):
        scrolled = Tix.ScrolledHList (self.toplevel, options="hlist.columns 3")

        self.hlist = scrolled.subwidget('hlist')
        self.hlist.configure ( separator="/",
                               background="white", foreground="black",
                               selectbackground="white", selectforeground="black")
        
      
        scrolled.pack(side=TOP, fill=BOTH, expand=1)
        scrolled.propagate(0)
        
        self.create_button_box()
        
        self.hlist.column_width(0, chars=1)
        self.hlist.column_width(1, chars=self.labelwidth)
        self.hlist.column_width(2, chars=self.entrywidth)
    
    def create_button_box(self):
        if self.showbuttons:
            self.buttonbox = Tix.ButtonBox(self.toplevel, pady=0)
            for b in self.buttons: self.add_button(b)
            self.buttonbox.pack (side=BOTTOM, anchor=W )        
        
    def build_form(self):
        for f in self.form.table:            
            if (f.name in Table.__special_columns__ 
                or f.name in self.excludefields): continue           
            form_element = self.create_form_element(f)
            self.set_label ( form_element, self.create_label(f) )
            self.set_entry ( form_element, self.create_entry(f) )

    def create_form_element(self, field):
        self.hlist.add ( field.name, itemtype=Tix.TEXT, text=" " )
        return field.name
            
    def create_label(self, field):
        return field.label

    def set_label(self, form_element, label):
        self.hlist.item_create ( form_element, 1, itemtype=Tix.TEXT, text=label)

    def create_entry(self, field):
        var = self.form.tkvars[field.name]
        if field.reference:
            if field.editor_class == "StaticReferenceEntry":
                entry = StaticReferenceEntry ( self, self.hlist, field )
            else:
                entry = ComboReferenceEntry ( self, self.hlist, field )
        elif field.type == "bit":
            entry = BooleanEntry (self, self.hlist, field)
        else:
            entry = TextEntry ( self, self.hlist, field )
            
        self.editor_widgets[field.name] = entry
        if field.name in self.disablefields: entry.disable()
        
        return entry
    
    def set_entry(self, form_element, entry):
        self.hlist.item_create ( form_element, 2, itemtype=Tix.WINDOW, window=entry.widget )
        
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
