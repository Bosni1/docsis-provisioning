from ProvCon.func import eventemitter
import wx, wx.combo

class mwxControl(object):
    Fonts = None
    def __init__(self):
        self.SetExtraStyle ( wx.TAB_TRAVERSAL )
    
    def CheckVariableValue(self, value):
        pass
    
    @staticmethod
    def GetEditorFont(name):
        if mwxControl.Fonts is None:            
            mwxControl.Fonts = {
                'Edit' : wx.Font ( 9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ),
                'Static' : wx.Font ( 11, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ),
                'Small' : wx.Font ( 7, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ),
            }
        return mwxControl.Fonts[name]

    def StateReset(self):
        """
        To be called when a control needs to be reset.
        Example: hide popup window of a combo ctrl, when the current record changes.
        """
        pass
    
class StaticText  (mwxControl, wx.StaticText):
    def __init__(self, *args, **kwargs):
        wx.StaticText.__init__ ( self, *args, **kwargs)
        mwxControl.__init__ ( self )
        self.SetFont ( self.GetEditorFont('Static')  )

class TextCtrl (mwxControl, wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        wx.TextCtrl.__init__ ( self, *args, **kwargs)
        mwxControl.__init__ ( self )
        self.SetFont ( self.GetEditorFont('Edit')  )
        
    
        
class ComboBox (mwxControl, wx.ComboBox):
    def __init__(self, *args, **kwargs):
        wx.ComboBox.__init__ ( self, *args, **kwargs)        
        mwxControl.__init__ ( self )
        self.SetFont ( self.GetEditorFont('Edit')  )
        

class CheckBox (mwxControl, wx.CheckBox):
    def __init__(self, *args, **kwargs):
        wx.CheckBox.__init__ ( self, *args, **kwargs)        
        mwxControl.__init__ ( self )
        self.reprfunc = kwargs.get ( "reprfunc", lambda x: str(x) )        
        
class RecordsComboPopup(wx.HtmlListBox, wx.combo.ComboPopup):        
    def __init__(self, **kwargs):
        self.PostCreate(wx.PreHtmlListBox())
        wx.combo.ComboPopup.__init__(self)
        self.records_changed_hook = None
        self.reprfunc = kwargs.get ( "reprfunc", lambda r: r._astxt)
        
    def SetRecords(self, recordlist):
        self.records = recordlist
        if self.records_changed_hook:
            self.records_changed_hook.remove()
            self.records_changed_hook = None
        self.populate_list()
        self.records_changed_hook = recordlist.listenForEvent ("record_list_changed", self.populate_list )
        
    def GetRecords(self):
        return self.records
    Records = property(GetRecords, SetRecords)

    def populate_list(self, *args):
        print "populate_list", args
        self.object_idx_hash = {}        
        for idx, r in enumerate(self.records):
            self.object_idx_hash[r.objectid] = idx 
        self.SetItemCount( len(self.records) + 1)
        self.Refresh()
    
    def SetCurrentOID(self, value):
        if value is None:
            self.Selection = 0
        else:
            self.Selection = self.object_idx_hash[value] + 1 
            self.Refresh()
        
        self.GetCombo().SetText( self.GetStringValue() )
        
    def GetCurrentOID(self):
        if self.Selection <= 0: return None
        try:
            return self.Records[self.Selection-1].objectid    
        except KeyError:
            return None
    CurrentOID = property(GetCurrentOID, SetCurrentOID)

    def GetCurrentRecord(self):
        if self.Selection <= 0: return None
        try:
            return self.Records[self.Selection-1]
        except KeyError:
            return None
        
    
    def Init(self):
        self.records = None
        
    def Create(self, parent):
        wx.HtmlListBox.Create (self, parent, 
                               style=wx.LC_NO_HEADER | wx.LC_REPORT | wx.LC_SINGLE_SEL )
        #self.Bind (wx.EVT_MOTION, self.OnMotion)
        self.Bind (wx.EVT_LEFT_UP, self.OnLeftUp)
        return True
    
    def GetControl(self):
        return self
        
    def GetStringValue(self):        
        n = self.Selection
        print "GetStringValue", n
        if n == 0:
            return ""
        elif n > 0:
            return self.Records[n-1]._astxt
        
    def OnGetItem(self, n):
        #print "??? OnGetItem ", n    
        if n == 0:
            return "(null)"
        else:
            return self.reprfunc(self.Records[n-1])
    
    #def OnPopup(self):
        #wx.combo.ComboPopup.OnPopup(self)

    #def OnDismiss(self):
        #wx.combo.ComboPopup.OnDismiss(self)
        
    #def PaintComboControl(self, dc, rect):
        #wx.combo.ComboPopup.PaintComboControl(self, dc, rect)
    
    #def OnComboKeyEvent(self, evt):
        #wx.combo.ComboPopup.OnComboKeyEvent(self, evt)
    
    #def OnComboDoubleClick(self, evt):
        #wx.combo.ComboPopup.OnComboDoubleClick(self, evt)
        
    def OnLeftUp(self, evt):
        self.Dismiss()   

    
class ComboCtrl(mwxControl, wx.combo.ComboCtrl):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = wx.CB_READONLY
        wx.combo.ComboCtrl.__init__(self, *args, **kwargs)
        mwxControl.__init__ (self)
        self.popup_ctrl = RecordsComboPopup( ** kwargs )
        self.SetPopupControl ( self.popup_ctrl )

        self.popup_ctrl.Bind (wx.EVT_LISTBOX, self.item_selected)        
        
    def item_selected(self, event, *args):
        print "SELECTED ", event.GetInt()        
        self.popup_ctrl.Dismiss()
        self.SetText ( self.popup_ctrl.GetStringValue() )
        self.update_variable()

class RecordListCombo(eventemitter, wx.combo.ComboCtrl):
            
    def __init__(self, parent, recordlist, *args, **kwargs):
        wx.combo.ComboCtrl.__init__(self, parent, style=wx.CB_READONLY)                
        eventemitter.__init__ (self,  [ "current_record_changed", "keyboard_command" ] )
        self.recordlist = recordlist
        self.popup_ctrl = RecordsComboPopup( **kwargs )
        self.SetPopupControl ( self.popup_ctrl )
        self.popup_ctrl.Records = self.recordlist
        self.set_null()
        self.popup_ctrl.Bind (wx.EVT_LISTBOX, self.item_selected) 
        self.Bind (wx.EVT_KEY_UP, self.key_pressed )     
        
        self.search_function = self.regex_search
    
    def regex_search(self, query, *args):
        pass
    
    def current_record(self):
        return self.popup_ctrl.GetCurrentRecord()

    def key_pressed(self, event, *args):
        if event.KeyCode == 13:
            self.raiseEvent ( "keyboard_command", "ENTER" )
        elif event.KeyCode == 27:
            self.raiseEvent ( "keyboard_command", "ESCAPE" )

    def set_null(self):
        self.popup_ctrl.CurrentOID = None

    def set_oid(self, oid):
        self.popup_ctrl.CurrentOID = oid

    def _process_item_selection(self):
        self.Refresh()        
        self.raiseEvent ( "current_record_changed", self.current_record() )
        
    def item_selected(self, event, *args):
        #Any exception raised here hangs my X, hence the handler
        wx.CallAfter (self._process_item_selection)
        event.Skip()        
        
Text = TextCtrl
Static = StaticText
Boolean = CheckBox
StaticReference = StaticText
ComboReference = ComboBox
ListReference = ComboCtrl
ArrayButton = wx.Button
