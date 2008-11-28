import wx
from os import getenv

artdir = getenv("PROVISIONING_ROOT") + "/lib/art/"

TB_SAVE = wx.Bitmap ( artdir + "rt_save.xpm", wx.BITMAP_TYPE_XPM )
TB_NEW = wx.Bitmap ( artdir + "rt_copy.xpm", wx.BITMAP_TYPE_XPM )
TB_RELOAD = wx.Bitmap ( artdir + "rt_undo.xpm", wx.BITMAP_TYPE_XPM )
