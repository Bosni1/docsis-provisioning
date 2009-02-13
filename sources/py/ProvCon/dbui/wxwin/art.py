from app import APP
import wx
from os import getenv, path

artdir = APP.ROOT + "/lib/art/"
client = wx.ART_TOOLBAR

TB_SAVE = wx.ArtProvider.GetBitmap ( wx.ART_FLOPPY, wx.ART_TOOLBAR, (16, 16) )
TB_DEL = wx.ArtProvider.GetBitmap ( wx.ART_DEL_BOOKMARK, wx.ART_TOOLBAR, (16, 16) )
TB_NEW = wx.ArtProvider.GetBitmap ( wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, (16, 16) )
TB_RELOAD = wx.ArtProvider.GetBitmap ( wx.ART_UNDO, wx.ART_TOOLBAR, (16, 16) )

TB = {}
TB["SAVE"] = TB_SAVE
TB["DEL"] = TB_DEL
TB["NEW"] = TB_NEW
TB["RELOAD"] = TB_RELOAD

class ArtStore:
    storedir = artdir + "auto/"
    def __init__(self):
        self._BITMAPS = {}
        
    def __getattr__(self, attrname):
        if attrname in self.__dict__: return self.__dict__[attrname]
        elif attrname in self._BITMAPS: return self._BITMAPS[attrname]
        else:
            if path.exists (self.storedir + attrname + ".png"):
                self._BITMAPS[attrname] = wx.Image (self.storedir + attrname + ".png").ConvertToBitmap()
                return self._BITMAPS[attrname]
            else:
                raise AttributeError(attrname)

BITMAPS = ArtStore()            