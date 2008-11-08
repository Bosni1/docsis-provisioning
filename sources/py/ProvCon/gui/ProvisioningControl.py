#!/bin/env python
# -*- coding: utf8 -*-


import sys
import Tix
import traceback, tkMessageBox
from Tkconstants import *
from ProvCon.pdb import *
import gettext

_ = gettext.gettext

TCL_DONT_WAIT           = 1<<1
TCL_WINDOW_EVENTS       = 1<<2
TCL_FILE_EVENTS         = 1<<3
TCL_TIMER_EVENTS        = 1<<4
TCL_IDLE_EVENTS         = 1<<5
TCL_ALL_EVENTS          = 0

class dictobj(dict):
    def __getattr__(self, attrname):
        if attrname in self:
            return self[attrname]
        return None
    
    def __setattr__(self, attrname, attrval):
        self[attrname] = attrval

class GridView(Tix.Grid):
    def __init__(self, *args, **kargs):
        kargs['editnotify'] = self.editnotify
        Tix.Grid.__init__(self, *args, **kargs)
    
    def editnotify(self, x, y):
        return False

class ObjectEditorModel(object):
    def __init__(self):
        self.type = None
        self.fields = {}
        self.vars = {}
        self.record = None
        
    def settype(self, typename):
        if self.type == typename: return
        try:
            sig = dbtuple.__signatures__[typename]
            self.fields = {}
            self.vars = {}
            self.record = None
            self.type = typename
            for f in sig:
                self.fields[f.name] = f
                self.vars[f.name] = Tix.StringVar()
        except KeyError:
            pass

    def getsignature(self, objectid):
        self.record = dbtuple ( objectid, resolve=True )
        #if self.record
        
class GenericObjectEditor(Tix.Frame):
    def __init__(self, *args, **kargs):
        Tix.Frame.__init__(self, *args, **kargs)
        self.record = None
        
    def setobject(self, objectid):
        self.record = dbtuple ( objectid, resolve=True, read=True )
        print self.record.tabular()
        
    def show(self):
        font = self.tk.eval ( "tix option get fixed_font" )
        print font
        for idx, f in enumerate(self.record._signature):
            label = Tix.Label ( self, text=f.name )
            var = Tix.StringVar ( value=self.record[f.name] )
            entry = Tix.Entry ( self, textvariable= var, font=font)
            label.grid ( column=0, row=idx )
            entry.grid ( column =1, row=idx )
            
            
        
class MainTab(Tix.Frame):
    def __init__(self, master=None, name=None):
        Tix.Frame.__init__(self, master)
        self.title = Tix.Label(self, text="List of objects" )
        self.title.grid ( column=0,row=0,columnspan=6, sticky=N )        
        
        objs = dbtuple.DB.query ( "SELECT * FROM pv.object").dictresult()
        for (cidx, v) in enumerate(objs[0]):
            Tix.Label ( self, text = v ).grid ( column=cidx, row= 1)            
        for (ridx, obj) in enumerate(objs):
            for (cidx, v) in enumerate(obj):
                l = Tix.Label ( self, text=obj[v] )                                
                l.grid (column=cidx, row=ridx+2)                        
            b = Tix.Button ( self, text="EDIT", command = lambda x=obj: self.editobj(x))
            b.grid ( column=cidx+1, row = ridx+2 )
        self.pack ( fill=X, expand=1)
        self.editor = None
        
    def editobj(self, obj):  
        if self.editor:
            self.editor.destroy()
        self.editor = GenericObjectEditor(self)
        self.editor.grid ( column=0, row=12, rowspan=10, columnspan=6 )
        self.editor.setobject ( obj['objectid'] )
        self.editor.show()
        
class TopLevelWindow:
    def __init__(self, root):
        self.root = root
        self.winfo = self.root.winfo_toplevel()
        self.winfo.wm_title ( "Provisioning Control" )
        self.winfo.geometry ("1000x800+10+10")
        self.exit = -1        
        self.winfo.wm_protocol ( "WM_DELETE_WINDOW", lambda self=self: self.shutdown() )

        self.frames = dictobj()
        
        self.frames.menu = self.create_main_menu()        
        self.frames.menu.pack ( side=TOP, fill=X )

        self.frames.status = self.create_status_bar()
        self.frames.status.pack ( side=BOTTOM, fill=X )
        
        self.frames.notebook = self.create_browser_notebook()
        self.frames.notebook.pack ( side=TOP, fill=BOTH, padx=4, pady=4, expand=1 )
        
        self.loop()
        self.destroy()
        
    def shutdown(self):
        self.exit = 0

    def create_main_menu(self):
        top = self.root
        mb = dictobj()
        m = dictobj()
        w = Tix.Frame(top, bd=2, relief=RAISED)

        mb.data = Tix.Menubutton (w, text=_("Data"), underline=0, takefocus=0)
        mb.data.pack ( side=LEFT )
        m.data = Tix.Menu(mb.data, tearoff=0)
        m.data.add_command ( label=_("New object"), underline=1)
        m.data.add_command ( label=_("Save object"), underline=1 )
        m.data.add_command ( label=_("Delete object"), underline=1 )
        m.data.add_command ( label=_("Reload object"), underline=1 )

        mb.data['menu'] = m.data        
        
        mb.reports = Tix.Menubutton (w, text=_("Reports"), underline=0, takefocus=0)
        mb.reports.pack ( side=LEFT )
        
        mb.tab = Tix.Menubutton (w, text=_("Tabs"), underline=0, takefocus=0)
        mb.tab.pack ( side = LEFT )
        
        m.tab = Tix.Menu (mb.tab, tearoff=0)
        m.tab.add_command ( label="Generic object form", underline=0 )
        mb.tab['menu'] = m.tab
            
        self.menubutton = mb
        self.menu = m
        
        return w

    def create_browser_notebook(self):
        w = Tix.NoteBook(self.root, ipadx=5, ipady=5, options = """
        tagPadX 6
        tagPadY 4
        borderWidth 2
        """)
        self.nbframes = dictobj()
        self.dyntabs = dictobj()        
        self.root['bg'] = w['bg'] 
        self.nbframes.main = w.add ( 'main', label="Main", underline=0 )
        self.dyntabs.main = MainTab ( self.nbframes.main )                                
                
        return w

    def create_status_bar (self):
        w = Tix.Frame (self.root, relief = RAISED, bd=1)
        self.status = Tix.Label (w, relief=SUNKEN, bd=1)
        self.status.form ( padx=3, pady=3, left=0, right='%70' )
        return w
    
    def loop(self):
        while self.exit < 0:
            try:
                while self.exit < 0:
                    self.root.dooneevent (TCL_ALL_EVENTS)
            except SystemExit:
                self.exit = 1
                return
            except KeyboardInterrupt:
                if tkMessageBox.askquestion ( 'Interrupt', 'Really quit?' ) == 'yes':
                    self.exit = 1
                    return
                continue
            except:
                t,v,tb = sys.exc_info()
                text = ""
                for line in traceback.format_exception(t,v,tb):
                    text += line + "\n"
                try: tkMessageBox.showerror ( u"Wyjątek!", text )
                except: print text
                self.exit = 1
                raise SystemExit, 1
    
    def destroy(self):
        self.root.destroy()
                

if __name__ == "__main__":
    root = Tix.Tk()
    try:
        TopLevelWindow(root)
    except:
        t,v,tb = sys.exc_info()
        text = ""
        for line in traceback.format_exception(t,v,tb):
            text += line + "\n"
        try: tkMessageBox.showerror ( _("Exception!"), text )
        except: print text
        
        
    