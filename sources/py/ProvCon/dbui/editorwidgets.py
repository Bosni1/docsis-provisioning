#!/bin/env python
import Tix
from Tkconstants import *
from orm import *
from forms import *
from gettext import gettext as _
from misc import *

class FieldEntry(object):
    """An abstract base class for field editors"""
    def __init__(self, formeditor, parent, field, **kwargs):
        self.parent = parent 
        self.formeditor = formeditor
        self.field = field
        self.form = self.formeditor.form
        self.variable = self.formeditor.form.tkvars[self.field.name]

    def disable(self):
        self.widget.config ( state='disabled' )
        
class TextEntry(FieldEntry):
    """A simple text entry"""
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.widget = Tix.Entry (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 disabledforeground="black",
                                 textvariable = self.variable)
        
class MemoEntry(FieldEntry):
    """A multi-line text entry"""
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        hgt = kwargs.get ( "height", 64 )
        self.widget = Tix.ScrolledText (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 height=64,
                                 scrollbar=Y )
                                                                  
        self.text = self.widget.subwidget('entry')
        self.text.config ( disabledforeground="black",textvariable = self.variable)

class StaticEntry(FieldEntry):
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.widget = Tix.Label (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 disabledforeground="black",
                                 textvariable = self.variable)    
        
class ReferenceEntry(FieldEntry):
    """An abstract base class for editors of fields that reference 
    other records"""
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

class ComboReferenceEntry(ReferenceEntry, eventemitter):
    """A 'classic' reference editor, which contains a combo-box with a list
    of records that may be referenced. Works for fields which have a small 
    number of possible values."""
    
    def __init__(self, *args, **kwargs):
        eventemitter.__init__ ( self, [ "navigate", "current_record_changed" ] )
        ReferenceEntry.__init__(self, *args, **kwargs)                        
        self.cmb_command = conditionalmethod(self.cmb_command)
        
        self.display_variable = Tix.StringVar()
        
        self.widget = Tix.ComboBox (self.parent, 
                                    editable=False, dropdown=True,
                                    options = "label.width 0 entry.width " + str(self.formeditor.entrywidth),                                     
                                    variable = self.display_variable,
                                    command=self.cmb_command)        
        self.entry = self.widget.subwidget ('entry')
        self.entry.config (disabledforeground="black")
        self.listbox = self.widget.subwidget('slistbox').subwidget('listbox')
        self.fill_records()
        
        self.current = None        
    
    def fill_records(self, *args):
        self.records = RecordList(self.field.reference)
        self.records.reload()
        for r in self.records:
            self.widget.insert (Tix.END, r._astxt)
        self.widget.insert (Tix.END, "<no object>" )
        
    def cmb_command(self, *args):  
        
        #Was the call initiated by the ComboBox constructor?
        if not hasattr(self, 'listbox'): return        
        try:
            self.value_change.freeze()        
            idx, = self.listbox.curselection()
            self.current = self.records[int(idx)]
            self.variable.set (self.current.objectid)
            self.emit_event ( "navigate", self.current.objectid )
            self.emit_event ( "current_record_changed", self.current )
        except IndexError:
            self.current = None
            self.variable.set (None)
            self.display_variable.set ( "<error> out of bounds" )
        finally:
            self.value_change.thaw()
    
    def value_change(self, *args):                
        """Handle a change in the field value initiated outside of 
        this editor"""                
        try:
            self.cmb_command.freeze()
            v = self.variable.get()
            self.current = None
            self.display_variable.set ( "" )
            if v is None or v == '': self.display_variable.set ( "<null> " )
            self.current = self.records.getid(int(v))
            self.display_variable.set ( self.current._astxt )
        except ValueError:
            pass            
        except KeyError:
            pass
        finally:
            self.cmb_command.thaw()
        
class SearchReferenceEntry(ComboReferenceEntry):
    def __init__(self, *args, **kwargs):
        eventemitter.__init__ ( self, [ "navigate", "current_record_changed" ] )
        ReferenceEntry.__init__(self, *args, **kwargs)                        

    def fill_records(self, *args):
        pass
    
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
            

###########################################################################################
## Array editors
## Array editors are widgets that allow editing sets of values, typically
## fields of type "array".
## An array editor may contain two subclasses:
## ItemEditor - an editor widget for array elements
## ButtonBox - a set of buttons which execute commands for each array element.            
class ArrayEntryTextMixin:    
    class ItemEditor(object):
        def __init__(self, arrayentry, idx):
            self.variable = Tix.StringVar()
            self.entry = Tix.Entry ( arrayentry.parent, textvariable=self.variable )
            self.tracecb = self.variable.trace ('w', partial(arrayentry.item_change, idx))
            self.entry.config ( width=arrayentry.formeditor.entrywidth )            
            arrayentry.editors.append (self)
            self.tracecb = None
            
        def destroy(self):
            if self.tracecb:
                self.variable.trace_vdelete ( 'w', self.tracecb )
            self.entry.forget()
            del self.entry, self.variable

class ArrayEntryButtonMixin:
    class ButtonBox(object):
        def __init__(self, arrentry,idx,_add=True,_del=True):
            self.frame = Tix.Frame ( arrentry.parent, width=arrentry.formeditor.commandwidth )
            if _add:
                self.bt_add = Tix.Button (self.frame, text='+', font=('Courier', 8, 'normal'), padx=0, pady=0, command=partial(arrentry.item_add, idx+1) )
                self.bt_add.pack(side=LEFT)
            if _del:
                self.bt_del = Tix.Button (self.frame, text='x', font=('Courier', 8, 'normal'), padx=0, pady=0, command=partial(arrentry.item_remove, idx) )            
                self.bt_del.pack(side=LEFT)
            if idx >= 0:
                arrentry.buttons.append (self)
        
        def destroy(self):
            self.frame.forget()
            del self.bt_add, self.bt_del, self.frame

class ArrayEntryComboMixin:
    class ItemEditor(object):
        def __init__(self, arrayentry, arrayidx):
            self.variable = Tix.StringVar()
            self.display_variable = Tix.StringVar()
            self.combo_selection = conditionalmethod(self.combo_selection)
            self.external_change = conditionalmethod(self.external_change)
            self.entry = Tix.ComboBox ( arrayentry.parent, 
                                        editable=False, dropdown=True,
                                        options = "label.width 0 entry.width " + str(arrayentry.formeditor.entrywidth),                                     
                                        variable=self.display_variable,
                                        command=self.combo_selection
                                        )
            self.listbox = self.entry.subwidget('slistbox').subwidget('listbox') 
            self.textbox = self.entry.subwidget('entry')
            self.textbox.config ( disabledforeground = "black" )
            self.value_idx = []
            self.disp_idx = []
            self.value_idx_map = {}
            if arrayentry.recordlist:
                for idx, r in enumerate (arrayentry.recordlist):
                    dispval = arrayentry.recorddispfunc (r)
                    self.value_idx.append (r.objectid)
                    self.value_idx_map[r.objectid] = idx
                    self.disp_idx.append (dispval)
                    self.entry.insert (Tix.END, dispval)
            elif arrayentry.choices:                
                for idx, (varval, dispval) in enumerate(arrayentry.choices):
                    self.value_idx.append(varval)
                    self.disp_idx.append (dispval)
                    self.value_idx_map[varval] = idx
                    self.entry.insert ( Tix.END, dispval )
            self.tracecb = self.variable.trace ('w', partial(arrayentry.item_change, arrayidx))
            self.localtrace = self.variable.trace ('w', self.external_change)
            arrayentry.editors.append (self)
            
        def external_change (self, *args):
            try:
                self.combo_selection.freeze()
                self.external_change.freeze()
                self.display_variable.set ( self.disp_idx[self.value_idx_map[int(self.variable.get())]] )
            except ValueError:
                self.display_variable.set ( self.variable.get() + " <no idx>" )
            except IndexError:
                self.display_variable.set ( self.variable.get() + " <no text>" )
            finally:
                self.external_change.thaw()
                self.combo_selection.thaw()
            
        def combo_selection(self, *args):
            print args
            idx, = self.listbox.curselection()
            self.combo_selection.freeze()
            self.variable.set ( self.value_idx[int(idx)] )            
            self.combo_selection.thaw()
            
        def destroy(self):        
            self.variable.trace_vdelete ( 'w', self.tracecb )        
            self.variable.trace_vdelete ( 'w', self.localtrace)
            self.entry.forget()
            del self.entry, self.variable
    
class ArrayEntryLabelMixin:
    class ItemEditor(object):        
        def __init__(self, arrayentry, idx):
            self.variable = Tix.StringVar()
            self.entry = Tix.Label ( arrayentry.parent, textvariable=self.variable )
        def destroy(self):
            del self.entry
            del self.variable
            
class ArrayEntry(FieldEntry):    
    """Abstract base class for array editor widgets"""
    def __init__(self, *args, **kwargs):
        FieldEntry.__init__(self, *args, **kwargs)
        self.value_change = conditionalmethod(self.value_change)        
        self.item_change = conditionalmethod(self.item_change)        
        self.branch = kwargs.get ( "branch", None )        
        self.recordlist = kwargs.get ("recordlist", None )
        self.recorddispfunc = kwargs.get ("recorddispfunc", lambda x: x._astxt )
        self.choices = kwargs.get ("choices", None )
        
        self.widget = Tix.Label (self.parent, 
                                 width=self.formeditor.entrywidth, 
                                 textvariable = self.variable)
        
        if hasattr(self, "ButtonBox"):
            self.default_buttons = self.ButtonBox (self, -1, _del=False)
            self.parent.item_create ( self.field.name, 3, itemtype = Tix.WINDOW, window=self.default_buttons.frame )
        
        self.buttons = []
        self.array = []
        self.editors = []
        
        self.variable.trace ( 'w', self.value_change )

    def redisplay_array(self, newarray):        
        if self.branch:                                
            for idx, val in enumerate(self.array):
                self.parent.delete_offsprings (self.field.name)
            for c in self.editors + self.buttons:
                c.destroy()
    
            self.buttons = []
            self.editors = []
            
            for idx, val in enumerate(newarray):
                                                
                self.parent.add (self.field.name+"/" + str(idx), itemtype=Tix.TEXT, text="+")                                        
                
                if hasattr(self, "ItemEditor"):
                    it = self.ItemEditor (self, idx )                                        
                    self.parent.item_create ( self.field.name+"/" + str(idx), 2, itemtype = Tix.WINDOW, window=it.entry )

                if hasattr(self, "ButtonBox"):
                    bb = self.ButtonBox(self, idx)                    
                    self.parent.item_create ( self.field.name+"/" + str(idx), 3, itemtype = Tix.WINDOW, window=bb.frame )
                
                it.variable.set ( val )
            self.array = newarray
        
    def value_change(self, *args):
        """A callback function called when the variable is changed outside of the
        widget (e.g. the edited record is changed)"""
        try:
            self.item_change.freeze()            
            self.redisplay_array(self.field.val_txt2py ( self.variable.get() ) or [])
        finally:
            self.item_change.thaw()
    
    def item_change(self, idx, *args):
        """A callback function called by ItemEditors when the item they hold
        changes value"""
        try:
            self.value_change.freeze()
            #rebuild the array from individual elements' values
            arr = map (lambda e: e.variable.get(), self.editors)
            self.variable.set ( self.field.val_py2txt ( arr ) )
            self.array = arr
        finally:
            self.value_change.thaw()
        
    def item_add (self, atidx, *args):
        """A callback function called when item addition is requested"""
        self.array.insert (atidx, ' ')
        self.item_change.freeze()
        #setting the variable to a new value will rebuild the ItemEditors
        self.variable.set (self.field.val_py2txt (self.array))
        self.item_change.thaw()
        
    
    def item_remove (self, idx, *args):
        """A callback function called when item removal is requested"""
        newarray = list(self.array)
        del newarray[idx]
        self.item_change.freeze()        
        self.variable.set (self.field.val_py2txt (newarray))
        self.redisplay_array (newarray)
        self.item_change.thaw()
        
        
class ArrayTextEntry(ArrayEntry, ArrayEntryTextMixin, ArrayEntryButtonMixin):
    pass


class ArrayStaticEntry(ArrayEntry, ArrayEntryLabelMixin):
    pass


class ArrayComboEntry(ArrayEntry, ArrayEntryComboMixin, ArrayEntryButtonMixin):
    pass
###########################################################################################

###########################################################################################

    