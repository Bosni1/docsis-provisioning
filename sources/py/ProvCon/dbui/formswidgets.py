#!/bin/env python
import Tix
from Tkconstants import *
from orm import *
from forms import *
from gettext import gettext as _
from misc import *
from editorwidgets import *

class GenericFormEditor(object):    
    """ 
    ==GenericFormEditor==
    """
    __defaults__ = [ 
        ( "labelwidth", 20 ),
        ( "entrywidth", 40 ),
        ( "commandwidth", 10),
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
        self.form.register_event_hook ( "current_record_changed", self.handle_form_record_changed )
        self.form.register_event_hook ( "current_record_modified", self.handle_form_record_modified )
        self.form.register_event_hook ( "current_record_saved", self.handle_form_record_saved )
    def create_toplevel(self):
        self.toplevel = Tix.Frame (self.parent)
        self.info_variable = Tix.StringVar()
        self.status_variable = Tix.StringVar()
        self.infobar = Tix.Label (self.toplevel, textvariable=self.info_variable,
                                  font=('Helvetica', 9, 'normal' ),
                                  padx=3, pady=2, justify=LEFT, anchor=W)
        self.infobar.pack (side=TOP, fill=X)

#        self.statusbar = Tix.Label (self.toplevel, textvariable=self.status_variable,
#                                   padx=20, relief=SUNKEN, anchor=W)
#        self.statusbar.pack (side=BOTTOM, fill=X, padx=5, pady=5)
        
        self.info_variable.set ( "[    ]" )
        self.status_variable.set ( "<null>" )

    def create_form_container(self):
        scrolled = Tix.ScrolledHList (self.toplevel, options="hlist.columns 4")

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
        self.hlist.column_width(3, chars=self.commandwidth)
    
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
        try:
            entry = getattr(self, "create_entry_" + field.name)(field)
            self.editor_widgets[field.name] = entry
            if field.name in self.disablefields: entry.disable()
            return entry
        except AttributeError:
            pass
            
        if field.isarray:
            if field.arrayof:                
                entry = ArrayComboEntry(self, self.hlist, field, branch=True,
                                        recordlist=RecordList(field.arrayof).reload() )
            else:
                entry = ArrayTextEntry(self, self.hlist, field, branch=True)
        elif field.reference:
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
    
    def handle_form_record_modified (self, record, *args):
        self.buttonbox.subwidget ( 'save' ).config ( bg = 'red' ) 
        
    def handle_form_record_saved (self, record, *args):
        self.buttonbox.subwidget ( 'save' ).config ( bg = 'grey' ) 
        
    def handle_form_record_changed (self, record, *args):
        self.info_variable.set ( str(record) )
        
class AbstractRecordListWidget(eventemitter):
    def __init__(self, *args, **kwargs):
        eventemitter.__init__ (self, [ 
            "current_record_changed", 
            "record_deleted",
            "navigate"
        ])
        
        self.records = []
        self.records_hash = {}
        
        self.parentform = kwargs.get ( "parentform", None )
        self.referencefield = kwargs.get ( "referencefield", None )        
        
        self.objecttype = kwargs.get ( "objecttype", "object" )
        self.allowsubclasses = kwargs.get ( "allowsubclasses", True )
        
        self.pager = kwargs.get ( "pager", None )
        self.records = kwargs.get ( "records", None )

        self.emitonbrowse = kwargs.get ( "emitonbrowse", True )
        self.recordtoolbox = kwargs.get ( "recordtoolbox", True )
        self.recordpopup = kwargs.get ( "recordpopup", True )        
        
        self.filterfunc = kwargs.get ( "filterfunc", lambda x: True )
        
        if self.parentform:
            self.parent_change_hook = self.parentform.register_event_hook ( "current_record_changed", self.parent_form_record_changed )
            
    def refreshDisplay(self):
        pass
        
    def setObjectIDs(self, objids):
        if self.pager:
            self.pager.setobjectids (objids)
            self.refreshDisplay()
        else:            
            self.setRecords ( [Record.ID (i) for i in objids] )
            
    def setRecords(self, recordlist):
        recordlist = filter (self.filterfunc, recordlist)
        if self.pager:
            self.pager.setrecords (recordlist)
        else:
            self.records = recordlist
            self.records_hash.clear()
            for r in self.records: self.records_hash[r.objectid] = r
        self.refreshDisplay()
    
    def getRecordById (self, objid):
        if self.pager:
            return self.pager.getrecordbyid (objid)
        else:
            return self.records_hash[objid]

    def update(self):
        if self.parentform:
            self.setObjectIDs ( Record.IDLIST ( self.objecttype, where = [ self.referencefield + ' = ' + str(self.parentform.current.objectid) ] ) )        

    def parent_form_record_changed(self, parentrecord, *args, **kwargs):        
        self.update()
        
class RecordListWidget(AbstractRecordListWidget):
    def __init__(self, parent, *args, **kwargs):
        AbstractRecordListWidget.__init__(self, *args, **kwargs)
        self.widget = Tix.ScrolledHList (parent, options="hlist.columns 4")
                                         
        self.hlist = self.widget.subwidget('hlist')
        self.hlist.config ( selectforeground="black", command = self.command_handler)
        if self.emitonbrowse:
            self.hlist.config ( browsecmd = self.command_handler)
        self.pack = self.widget.pack
        self.current_selected_record = None            
        
    def append_list_item(self, r):
        self.hlist.add ( r.objectid, itemtype=Tix.TEXT, text=str(r.objectid) )            
        self.hlist.item_create ( r.objectid, 1, itemtype=Tix.TEXT, text=r._astxt )
    
    def append_list_item_table_info(self, r):
        self.hlist.add ( r.objectid, itemtype=Tix.TEXT, text=str(r.objectid) )            
        self.hlist.item_create ( r.objectid, 1, itemtype=Tix.TEXT, text=r.name)

    def append_list_item_field_info(self, r):
        self.hlist.add ( r.objectid, itemtype=Tix.TEXT, text=str(r.objectid) )            
        self.hlist.item_create ( r.objectid, 1, itemtype=Tix.TEXT, text=r.name)
        self.hlist.item_create ( r.objectid, 2, itemtype=Tix.TEXT, text=r.type)
        
    def refreshDisplay(self):
        self.hlist.delete_all()        
        for r in self.records:
            try:
                getattr(self, "append_list_item_" + r.objecttype)(r)
            except AttributeError:
                self.append_list_item ( r )
    
    def command_handler(self, idx, *args):        
        if self.current_selected_record != idx:
            self.current_selected_record = idx
            record = self.getRecordById (int(idx))
            self.emit_event ( "current_record_changed", record )
            self.emit_event ( "navigate", record.objectid )