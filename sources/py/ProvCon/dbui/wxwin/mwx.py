import wx

class mwxControl(object):
    Fonts = None

    def CheckVariableValue(self, value):
        pass

    def GetEditorFont(self, name):
        if mwxControl.Fonts is None:            
            mwxControl.Fonts = {
                'Edit' : wx.Font ( 10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ),
            }
        return mwxControl.Fonts[name]
    
class StaticText  (mwxControl, wx.StaticText):
    def __init__(self, *args, **kwargs):
        wx.StaticText.__init__ ( self, *args, **kwargs)
        self.SetFont ( self.GetEditorFont('Edit')  )

class TextCtrl (mwxControl, wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        wx.TextCtrl.__init__ ( self, *args, **kwargs)
        self.SetFont ( self.GetEditorFont('Edit')  )
    
        
class ComboBox (mwxControl, wx.ComboBox):
    def __init__(self, *args, **kwargs):
        wx.ComboBox.__init__ ( self, *args, **kwargs)        
        self.SetFont ( self.GetEditorFont('Edit')  )
        

class CheckBox (mwxControl, wx.CheckBox):
    pass

Text = TextCtrl
Static = StaticText
Boolean = CheckBox
StaticReference = StaticText
ComboReference = ComboBox

ArrayButton = wx.Button
