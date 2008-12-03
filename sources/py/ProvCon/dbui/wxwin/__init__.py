import fields, forms, navigators, recordlists, complete
# -*- coding: utf8 -*-

def DBErrorHandler(exc):
    import wx, sys, traceback
    _,_,tb = sys.exc_info()
    
    class Popup(wx.Frame):
        def __init__(self):
            wx.Frame.__init__ (self, None, title="Błąd podczas operacji na bazie danych!", size=(500, 400))
            self.Center()
            sizer = wx.BoxSizer ( wx.VERTICAL )            
                        
            self.stacklist = wx.ListCtrl ( self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL )
            self.stacklist.InsertColumn(0, "File")
            self.stacklist.InsertColumn(1, "Line")            
            self.stacklist.InsertColumn(2, "Function")
            self.stacklist.InsertColumn(3, "")
                                    
            self.txt = wx.StaticText ( self, label =  exc.__repr__() )            
            self.txt.SetFont ( wx.Font ( 10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ) )

            sizer.Add ( self.txt, 5, flag=wx.EXPAND )
            sizer.Add ( self.stacklist, 10, flag=wx.EXPAND )
            
            tbl = traceback.extract_tb (tb)            
            for idx, (f,ln,fn,tx) in enumerate(tbl):
                from os.path import split
                _,f = split(f)
                self.stacklist.InsertStringItem (idx, f)
                self.stacklist.SetStringItem (idx, 1, str(ln) )
                self.stacklist.SetStringItem (idx, 2, fn )
                self.stacklist.SetStringItem (idx, 3, tx )
            self.stacklist.SetColumnWidth (3, wx.LIST_AUTOSIZE )                

            self.SetSizer ( sizer )
            
            
    Popup().Show()
        