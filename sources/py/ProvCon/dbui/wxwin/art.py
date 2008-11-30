import wx
from os import getenv

artdir = getenv("PROVISIONING_ROOT") + "/lib/art/"
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