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
        ( "showinfo", True),
        ( "showhandle", True),
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
        
        self.handlevar = Tix.StringVar()
        self.handlebar = Tix.Button (self.toplevel, anchor=N, width=1, textvariable=self.handlevar, padx=2, pady=2, borderwidth=1)
        if self.showhandle:
            self.handlebar.pack ( side=LEFT, fill=Y, padx=4)
        
        self.infobar = Tix.Label (self.toplevel, textvariable=self.info_variable,
                                  font=('Helvetica', 9, 'normal' ),
                                  padx=3, pady=2, justify=LEFT, anchor=W)
        if self.showinfo:
            self.infobar.pack (side=TOP, fill=X)
                
        self.info_variable.set ( "[    ]" )        

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
            for b in self.buttons: 
                print b, self._button_label_.get(b, (b,None))[0]
                self.add_button(b)                
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
        #if this class has a "create_entry_<fieldname>" attribute, 
        #use it to create this entry
        try:
            entry = getattr(self, "create_entry_" + field.name)(field)
            self.editor_widgets[field.name] = entry
            if field.name in self.disablefields: entry.disable()
            return entry
        except AttributeError:
            pass
        options = {}
        options.update ( field.editor_class_params )        
        #else use the default
        cls = Entry.Text    #the 'default default' :)
        if field.isarray:
            if field.arrayof:                
                cls = Entry.ArrayCombo
                options["recordlist"] = RecordList(field.arrayof).reload()
            else:
                classname = "Array" + field.editor_class                
                try:
                    cls = getattr(Entry, classname)
                except AttributeError:
                    cls = Entry.ArrayText 
            options["branch"] = True            
        elif field.reference:
            classname = field.editor_class + "Reference"
            try:
                cls = getattr(Entry, classname)
            except AttributeError:
                cls = Entry.ComboReference
        else:
            classname = field.editor_class
            try:
                cls = getattr(Entry, classname)
            except AttributeError:        
                if len(field.choices) > 0:
                    cls = Entry.Combo                    
                else:
                    cls = Entry.Text

        
        entry = cls(self, self.hlist, field, **options)
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

    def handle_handle_clicked(self, *args):
        pass
    
    def add_button(self, buttonname, **kwargs):
        self.buttonbox.add ( buttonname, 
                             text=self._button_label_.get(buttonname, (buttonname,None))[0], 
                             command=lambda *x: self.button_command(buttonname, *x) )
    
    def handle_form_record_modified (self, record, *args):
        self.handlevar.set ( '*' )
        self.handlebar.config ( fg = 'red' )
        
    def handle_form_record_saved (self, record, *args):
        self.handlevar.set ( '' )
        self.handlebar.config ( fg = 'black' )

        
    def handle_form_record_changed (self, record, *args):
        self.info_variable.set ( str(record) )
        
class AbstractRecordListWidget(eventemitter):
    def __init__(self, *args, **kwargs):
        eventemitter.__init__ (self, [ 
            "current_record_changed", 
            "current_record_deleted",
            "current_record_modified",
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
            return self.pager.getrecordbyid (int(objid))
        else:
            return self.records_hash[int(objid)]

    def update(self):
        if self.parentform:
            self.setObjectIDs ( Record.IDLIST ( self.objecttype, where = [ self.referencefield + ' = ' + str(self.parentform.current.objectid) ] ) )        

    def parent_form_record_changed(self, parentrecord, *args, **kwargs):        
        self.update()


            
class RecordListFormatter:
    """comment this ASAP, before you forget all this crap"""
    def __init__(self, recordlist, **kwargs):
        self.recordlist = recordlist
        self.columns = kwargs.get ( "columns", 1 )
        self.reprfunc = kwargs.get ( "reprfunc", lambda r,col: r._astxt )
        self.stylefunc = kwargs.get ( "stylefunc", lambda r,col: None )
    
    def item_object (self, record, column, reprstr, style, **kwargs):        
        return (Tix.TEXT, reprstr, style)

    def insert_item (self, hlist, record):        
        hlist.add ( record.objectid, itemtype=Tix.TEXT, text="" )            
        it, txt, style = self.get_item ( record, 0 )
        hlist.item_create ( record.objectid, 0, itemtype=it, text=txt, style=style )
            
    def get_item (self, record, column, *args, **kwargs):
        datatype = record.objecttype
        reprfunc = find_method_for_superclass (self, "repr", record, self.reprfunc )
        itemfunc = find_method_for_superclass (self, "item", record, self.item_object )
        stylefunc = find_method_for_superclass (self, "style", record, self.stylefunc )
        return itemfunc (record, column, reprfunc(record, column), stylefunc(record, column) )

class RecordListToolbox:
    def __init__(self, recordlist, **kwargs):
        self.recordlist = recordlist
        
    def insert_buttons(self, hlist, record, **kwargs):
        column = self.recordlist.formatter.columns
        frame = Tix.Frame (hlist, padx=0, pady=0)
        
        for tbitem in record._table.recordlisttoolbox:
            commandid, txt = tbitem.split ("//")
            stylefn = find_method_for_superclass (self, "style_" + commandid, record, lambda x: None )            
            bt = Tix.Label ( frame,  text=txt, bg='white', fg='black')
            bt.pack (side=LEFT,padx=2,pady=0,ipadx=0,ipady=0)
        #frame.pack (expand = 1, fill=X)
        hlist.item_create ( record.objectid, column, itemtype=Tix.WINDOW, window=frame)
        
    def invoke(self, commandid, record):
        method = find_method_for_superclass (self, "invoke_" + commandid, record, lambda x: None )
        return method(record)

class RecordListPopup:
    def __init__(self, recordlist, **kwargs):
        self.recordlist = recordlist
        self.menus = {}
        
    def popup(self, event, record, *args,  **kwargs):        
        if record.objecttype not in self.menus:        
            self.build_menu ( record )        
        
        if self.menus[record.objecttype]:        
            #try:
            print record
            self.menus[record.objecttype].tk_popup ( event.x_root, event.y_root, 0)
            #finally:
            #    self.menus[record.objecttype].grab_release()
                
    def build_menu (self, record):
        table = record._table        
        if len(table.recordlistpopup) > 0:
            menu = Tix.Menu ( self.recordlist.widget, tearoff=0 )
            for p in table.recordlistpopup:
                cmdid, lbl = p.split("||")[:2]
                menu.add_command ( label=lbl )
                print lbl, cmdid            
            self.menus[record.objecttype] = menu
            
        
    def invoke(self, commandid, record):
        method = find_method_for_superclass (self, "invoke_" + commandid, record, lambda x: None )
        return method(record)


class RecordListWidget(AbstractRecordListWidget):
    def __init__(self, parent, *args, **kwargs):
        AbstractRecordListWidget.__init__(self, *args, **kwargs)
        self.formatter = kwargs.get("formatter", RecordListFormatter(self))
        self.toolbox = kwargs.get("toolbox", RecordListToolbox(self) )
        self.popup = kwargs.get("popup", RecordListPopup(self) )        

        self.width = kwargs.get("width", [None for i in xrange(0,self.formatter.columns)] )
        self.parent = parent
        
        columns = self.formatter.columns + 1
        self.widget = Tix.ScrolledHList (parent, options="hlist.columns " + str(columns))
                                    
        self.hlist = self.widget.subwidget('hlist')
        self.hlist.config ( selectforeground="black", command = self.command_handler)
        
        self.hlist.bind ( "<3>", self.popup_menu )
        if self.emitonbrowse: self.hlist['browsecmd'] = self.command_handler

        for idx, w in enumerate(self.width): 
            objid =self.hlist.column_width (idx, w)
            
        
        self.pack = self.widget.pack        
        self.current_selected_record = None            

    def popup_menu(self, event):
        record = self.getRecordById ( self.hlist.nearest (event.y) )
        self.popup.popup ( event, record )
        
    def append_list_item(self, r):
        self.hlist.add ( r.objectid, itemtype=Tix.TEXT, text=str(r.objectid) )            
        self.hlist.item_create ( r.objectid, 1, itemtype=Tix.TEXT, text=r._astxt )    
        
    def refreshDisplay(self):
        tbcolumn = self.formatter.columns
        self.hlist.delete_all()        
        for r in self.records:
            self.formatter.insert_item (self.hlist, r)
            self.toolbox.insert_buttons(self.hlist, r)
    def command_handler(self, idx, *args):        
        if self.current_selected_record != idx:
            self.current_selected_record = idx
            record = self.getRecordById (int(idx))
            self.emit_event ( "current_record_changed", record )
            self.emit_event ( "navigate", record.objectid )
            