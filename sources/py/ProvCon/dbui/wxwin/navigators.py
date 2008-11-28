from ProvCon.dbui.abstractui.navigators import BaseNavigator
import art
import wx

class Navigator(BaseNavigator, wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        BaseNavigator.__init__ ( self, *args, **kwargs )
        wx.Panel.__init__ ( self, parent )
        self.sizer = wx.BoxSizer ( wx.HORIZONTAL )

        button_opt = { 'style' : wx.BU_EXACTFIT }
        elements = []

        
        labels = {}
        for bname in [ "first", "prev", "next", "last"]:
            elements.append ( wx.Button ( self, label=labels.get(bname, bname), name=bname, **button_opt ) )
        
        for b in elements:
            b.SetFont (wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))            
            b.Bind ( wx.EVT_BUTTON,getattr(self, b.Name) )
            
        txt = wx.TextCtrl (self)
        txt.SetFont ( wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD) )
        txt.SetForegroundColour ( wx.NamedColor ( "blue" ) )
        txt.SetBackgroundColour ( wx.NamedColor ( "yellow") )

        self.infotext = txt
        
        self.sizer.Add ( elements[0], 0 )
        self.sizer.Add ( elements[1], 0 )
        self.sizer.Add ( txt, 10, flag=wx.EXPAND )
        self.sizer.Add ( elements[2], 0 )
        self.sizer.Add ( elements[3], 0 )
        
        self.SetSizer (self.sizer)
    
    def update(self):
        self.infotext.SetValue ( self.currentdisplay() )
        
        