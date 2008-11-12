#!/bin/env python
# -*- coding: utf8 -*-
from orm import *
import Tix
from Tkconstants import *
import tkCommonDialog
import tkMessageBox, traceback
from gettext import gettext as _

def partial (f, *defargs, **defkwargs):
    ""
    def _f(*largs, **lkwargs):
        args = defargs + largs        
        return f( *args, **lkwargs )
    return _f

class Form(object):
    def __init__(self, table):
        self.table = table
        self.current = Record.EMPTY (table.name)
        self.tkvars = {}
        for f in self.table:
            self.tkvars[f.name] = Tix.StringVar()
            self.tkvars[f.name].trace ( 'w', partial (self.value_change_handler, f.name) ) 
        #when this is set, changes to tkvars are not propagated to
        #the record
        self.disable_value_change_handler = False
    def save(self):
        self.current.write()

    def reload(self):
        self.current.read()

    def new(self):
        pass

    def setid(self, objectid):
        self.current.setObjectID ( objectid )
        self.disable_value_change_handler = True
        self.on_record_changed_handler()
        self.disable_value_change_handler = False
        
    def delete(self):
        pass

    def on_edit_handler (self, fieldname):        
        self.current.setFieldStringValue ( fieldname, self.tkvars[fieldname].get() )
            
    def value_change_handler(self, fname, *args):                
        if self.disable_value_change_handler: return
        if fname in self.table: self.on_edit_handler ( fname )
                    
    def on_record_changed_handler(self):
        for f in self.table:
            self.tkvars[f.name].set ( self.current.getFieldStringValue ( f.name ) )
    
def BaseSpecializedForm(table):
    class _Form(Form):
        def __init__(self):
            Form.__init__(self, table)
    return _Form        
    
class Navigator(object):
    def __init__(self):
        self.records = []
        self.currentidx = 0

    onrecordchange = lambda self, idx: self
        
    def navigate (self, relative):
        return self.navigateabsolute (self.currentidx + relative )        
    
    def navigateabsolute (self, idx):
        if len(self) == 0: return None
        if idx > len(self): idx = idx - len(self)
        if idx <= 0: idx = len(self) + idx
        self.currentidx = idx
        self.onrecordchange (idx)
        return self.current()
    
    def setrecords (self, rl):
        self.records = rl
        if len(rl) > 0: self.navigateabsolute(1)
        
    def current(self):
        return self.records[self.currentidx - 1]
    
    def currentid(self):
        return self.current()['objectid']
    
    def __len__(self):
        return len(self.records)

    def next(self):
        return self.navigate(1)
    
    def prev(self):
        return self.navigate(-1)
    
    def first(self):
        return self.navigateabsolute(1)

    def last(self):
        return self.navigateabsolute( len(self) )
    

class NavigatorWidget (Tix.Frame, Navigator):
    def __init__(self, parent, form, *args, **kwargs):
        Tix.Frame.__init__(self, parent, *args, **kwargs)
        Navigator.__init__(self)
        self.__form = form        
        self.buttons = {
            "prev" : Tix.Button (self, padx=4, pady=1, width=3, text="<<", command=self.prev),
            "next" : Tix.Button (self, padx=4, pady=1, width=3, text=">>", command=self.next),
            "save" : Tix.Button (self, padx=4, pady=1, width=3, text=">>", command=self.__form.save),
        }
        self.inputvar = Tix.StringVar()
        self.entry = Tix.Entry (self, width=40, textvariable = self.inputvar )        
        for i, b in enumerate(self.buttons.values()): b.pack (side=LEFT )
        self.entry.pack (side=RIGHT, fill=X )
        self.notify = []
        
    def onrecordchange(self, idx):
        self.inputvar.set ( self.current()['txt'] )
        for n in self.notify: n()
        
class TabularObjectEditor(Tix.Frame):
    def __init__(self, master, form, *args, **kwargs):
        #kwargs['label'] = kwargs.get ("label", form.table.label)
        #kwargs['options'] = kwargs.get ("options", """
        #borderWidth 2
        #""")
        Tix.Frame.__init__(self, master, *args, **kwargs)
        
        self.__form = form
        self.controls = {}
        self.editingframe = Tix.LabelFrame (self, label="Editor")

        
        for idx, f in enumerate(self.__form.table):
            if f.name in Table.__special_columns__: continue
            if f.reference:
                e = StaticReferenceWidget(self.editingframe, f, self.__form)
            elif f.isarray:
                e = ArrayEditorWidget(self.editingframe, f, self.__form)
            else:
                e = ValueEditorWidget (self.editingframe, f, self.__form)
            l = e.label
            self.controls[f.name] = (e,None)
            l.grid(row=idx, column=0)
            e.grid(row=idx, column=1)

        #self.editingframe.pack ( side=TOP, fill=BOTH )
            
#        self.toolboxframe = Tix.Frame (self)
#        self.toolboxframe.form ( left=0, top=self.editingframe )
        
#        self.action = Tix.Button (self.toolboxframe, text="Action!", command = self.onAction )
#        self.action.pack()
                        
        self.nav = NavigatorWidget(self, self.__form)
        #self.nav.pack (side=BOTTOM, fill=X)
        self.nav.records = self.__form.table.recordlist()
        self.nav.notify.append ( self.onrecordchanged )
        self.nav.navigateabsolute(0)
    
    def onrecordchanged(self, *args):
        self.__form.setid ( self.nav.currentid() )
    
    def onAction(self):
        tkMessageBox.showinfo ( 'action', self.form.current.PP_TABLE )

class StaticReferenceWidget(Tix.Frame):
    def __init__(self, master, field, form, *args, **kwargs):
        Tix.Frame.__init__(self, master, *args, **kwargs)
        self.field = field
        self.__form = form

        self.tkvar = self.__form.tkvars[field.name]
        self.tkvar.trace ( 'w', self.value_change_handler )         
        self.disable_external_update_handler = False

        self.label = Tix.Label ( master, text = field.label )
        self.dispvar = Tix.StringVar()
        self.editor = Tix.Label ( self, textvariable = self.dispvar )
        self.editor.pack (fill=X)
        self.referencedrecord = Record()
    
    def value_change_handler(self, *args):          
        if self.disable_external_update_handler: return
        try:
            objectid = int(self.tkvar.get())
        except ValueError:
            self.dispvar.set ( "<empty>" )
            return        
        self.referencedrecord.setObjectID (objectid)
        self.dispvar.set ( self.referencedrecord._astxt )
        
        

class ValueEditorWidget(Tix.Frame):
    def __init__(self, master, field, form, *args, **kwargs):
        Tix.Frame.__init__(self, master, *args, **kwargs)
        self.field = field
        self.__form = form
        #the tkvar traced back to the record value
        self.tkvar = self.__form.tkvars[field.name]
        #we need this to build subwidgets
        self.ve_parent = master
        #subwidgets
        self.ve_label = None
        self.ve_entry = None 
        self.ve_entry = self.entry
                
    def get_entry(self):
        """The entry widget is created on first access to the property"""
        if self.ve_entry is None:
            self.ve_entry = Tix.Entry ( self, textvariable=self.tkvar )
            self.ve_entry.pack ( fill = X, expand=1 )
    entry = property(get_entry)
        
    def get_label(self):
        """The label widget is created on first access to the property"""
        if self.ve_label is None: 
            self.ve_label = Tix.Label ( self.ve_parent, text = self.field.label )
        return self.ve_label
    label = property (get_label)

class ArrayEditorWidget(ValueEditorWidget):
    """A winbox-like widget to edit array values."""
    def __init__(self, master, field, form, *args, **kwargs):
        ValueEditorWidget.__init__ (self, master, field, form, *args, **kwargs)
        #We keep a tkvar for each array element
        self.tkelemvars = []
        #Every update to the record's tkvar triggers an update of this
        #widget's tkvars.
        self.tkvar.trace ( 'w', self.value_change_handler ) 
        #this array holds the actual values of the elements
        self.array = []
        self.controls = []        
        self.bplus = None 
        #these flags disable tkvar value change handlers to avoid
        #infinite recursion, since update of the record value
        #triggers a change of the internal values and vice versa
        self.disable_external_update_handler = False
        self.disable_internal_update_handler = False
        
    def get_entry(self):
        if self.ve_entry is None:
            self.ve_entry = Tix.Frame ( self)
            self.ve_entry.pack ( fill = BOTH )            
        return self.ve_entry
    entry = property(get_entry)
        
    def value_change_handler(self, *args):          
        """Handle a change of the record's value"""
        if self.disable_external_update_handler: return
        self.array = self.field.val_txt2py ( self.tkvar.get() )
        self.rebuild()

    def item_update_handler(self, idx, *args):
        """Handle a change of one of the element's values
        (triggered by UI) """
        if self.disable_internal_update_handler: return        
        self.array[idx] = self.controls[idx][3].get()  

        self.disable_external_update_handler = True
        self.update_record()
        self.disable_external_update_handler = False
    
    def update_record(self):
        """Copy the current edited value to the record"""
        self.tkvar.set ( self.field.val_py2txt (self.array) )        

    def clear(self):
        """Reset the UI"""
        for e,bp,bd,v,cbname in self.controls:
            e.grid_forget()
            bp.grid_forget()
            bd.grid_forget()            
            v.trace_vdelete('w', cbname)
            del e
            del bp
            del bd            
            del v
        self.controls = [] 
        if self.bplus: 
            self.bplus.pack_forget()
            self.bplus = None

    def insert_item(self, idx, *args):
        print "insert", idx
        if self.array is None: self.array = []        
        print self.array
        if idx == len(self.array):
            self.array.append('')
        else:
            self.array.insert(idx, '')
        print self.array
        self.update_record()

    def remove_item(self, idx, *args):
        if self.array is None: return
        del self.array[idx]
        self.update_record()
    
    def rebuild(self):        
        self.clear()
        if self.array is None or len(self.array) == 0:
            self.bplus = Tix.Button ( self.entry, text='+', font=('Courier', 8, 'normal'), padx=0, pady=0, command=partial(self.insert_item, 0) )                  
            self.bplus.pack(side=RIGHT)
        else:
            
            for idx, v in enumerate(self.array):
                var = Tix.StringVar()
                var.set ( v )
                entry = Tix.Entry (self.entry, textvariable=var)
                bplus = Tix.Button ( self.entry, text='+', font=('Courier', 8, 'normal'), padx=0, pady=0, command=partial(self.insert_item, idx+1) )                
                bdel = Tix.Button ( self.entry, text='x', font=('Courier', 8, 'normal'), padx=0, pady=0, command=partial(self.remove_item, idx) )
                bplus.grid ( row=idx, column=1 )
                bdel.grid ( row=idx, column=2 )
                entry.grid ( row=idx, column=0 )                
                cbname = var.trace ( 'w', partial(self.item_update_handler, idx) )
                self.controls.append ( (entry, bplus, bdel, var,cbname) )
                
    
#root = Tix.Tk()
#print root
#wm = root.winfo_toplevel()
#wm.geometry( "800x600+10+10" )
#f = Form ( Table.Get ( "field_info" ) )
##f.setid ( 1 )            
#tf = TabularObjectEditor ( root, f)
#tf.pack()
#exitloop = -1

#def report_callback_exception(exc, val, tb):
    #text = ""
    #for line in traceback.format_exception(exc,val,tb):
        #text += line + "\n"
    #tkMessageBox.showerror ( _("Error"), message=text )
#root.report_callback_exception = report_callback_exception
#root.mainloop()
