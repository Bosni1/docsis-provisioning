import fields, forms, navigators, recordlists, complete


def DBErrorHandler(*args):
    import wx
    wx.MessageBox ( str (args) )