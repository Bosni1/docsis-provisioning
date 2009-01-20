import ProvCon.dbui.orm as orm
import ProvCon.dbui.meta as meta
import wx
import wx.lib.mvctree as tree

class LocationTreeRoot:
    def __init__(self):
        self.records = orm.RecordList ( meta.Table.Get("city"), select=["name"], order='name' )                        
        self.records.reload()
        self.parent = None
        self.children = map ( lambda x: None, self.records )

    def GetChildCount(self):    
        return len(self.children)
        
    def GetChildAt(self, index):        
        if self.children[index] is None:
            self.children[index] = CityNode (self.records[index], self)
        return self.children[index]
        
    def isLeaf(self):
        return False
    
    def __str__(self):
        return "Lokalizacje"

class MyNode:
    def __init__(self, record, parent):
        self.record = record
        self.parent = parent
        self.children = []
        self.records = []
        self._reloaded = False
    
    def __str__(self):        
        return self.record._astxt

    def GetChildCount(self):                
        if not self._reloaded:
            self.records.reload()
            self.children = map ( lambda x: None, self.records )    
            self._reloaded = True
        return len(self.children)
        
    def GetChildAt(self, index):        
        if self.children[index] is None:
            self.children[index] = self.__childclass__ (self.records[index], self)
        return self.children[index]
    
    def IsLeaf(self):
        #return len(self.children) == 0
        return False
    
    
class CityNode(MyNode):
    def __init__(self, record, parent):
        MyNode.__init__(self, record, parent)        
        self.records = orm.RecordList ( meta.Table.Get("street"), select=["name", "prefix"], 
                                      order='name', 
                                      _filter = 'cityid = %d' % record.objectid )        
        self.__childclass__ = StreetNode
        
        
class StreetNode(MyNode):
    def __init__(self, record, parent):
        MyNode.__init__(self, record, parent)        
        self.records = orm.RecordList ( meta.Table.Get("building"), select=["number"], 
                                      order='number', 
                                      _filter = 'streetid = %d' % record.objectid )        
        self.__childclass__ = BuildingNode

    def __str__(self):
        return self.record.prefix + "." + self.record.name

class BuildingNode(MyNode):
    def __init__(self, record, parent):
        from ProvCon.dbui.di import rLocation
        MyNode.__init__(self, record, parent)        
        self.records = orm.RecordList ( meta.Table.Get("location"), select=["number", "handle"], 
                                      order='number', 
                                      recordclass=rLocation,
                                      _filter = 'buildingid = %d' % record.objectid )        
        self.__childclass__ = LocationNode
    
class LocationNode(MyNode):
    def __init__(self, record, parent):
        MyNode.__init__(self, record, parent)                
        self.handle = self.record.getGenericHandle()
        
    def IsLeaf(self):
        return True

    def __str__(self):
        return self.handle 
    
    
class LocationTreeModel(tree.TreeModel):
    def __init__(self):
        self.root = LocationTreeRoot()
        
    def GetRoot(self):
        return self.root

    def SetRoot(self):
        pass    

    def GetChildCount(self, node):        
        return node.GetChildCount()
        
    def GetChildAt(self, node, index):
        return node.GetChildAt(index)
        
    def GetParent(self, node):        
        return node.parent
        
    def AddChild(self, parent, child):
        print parent, child
        if hasattr(self, 'tree') and self.tree:
            self.tree.NodeAdded(parent, child)
            
    def RemoveNode(self, child):
        if hasattr(self, 'tree') and self.tree:
            self.tree.NodeRemoved(child)
            
    def InsertChild(self, parent, child, index):
        if hasattr(self, 'tree') and self.tree:
            self.tree.NodeInserted(parent, child, index)
            
    def IsLeaf(self, node):
        return node.IsLeaf()
    
    def IsEditable(self, node):
        return False
    def SetEditable(self, node):
        return False
    
class LocationEditor(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        sizer = wx.BoxSizer (wx.HORIZONTAL)            
        
        self.split = wx.SplitterWindow (self)
        self.tree = tree.MVCTree (self.split, -1)
        self.tree.SetAssumeChildren(True)
        self.tree.SetModel ( LocationTreeModel() )                        
        
        tmp = wx.StaticText (self.split, label="EDITOR" )
        
        self.split.SetMinimumPaneSize ( 200 )
        self.split.SplitVertically ( self.tree, tmp, -100 )

        self.SetSizer(sizer)        
        sizer.Add (self.split, 4, wx.EXPAND )
        
        
        
        
        