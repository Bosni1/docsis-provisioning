#!/bin/env python
from app import APP
import socket, sys, os
try:
    import readline
    hasReadline = True
except ImportError:
    hasReadline = False

import atexit

class CliNode(object):
    def __init__(self, name, **kkw):        
        self._children = []
        self._children_idx = {}
        self.name = name
        self._parent = kkw.get ( "parent", None )
        if self._parent:
            self._parent.addChild (self)
        self.root = False
        self._sig = kkw.get ("signature", {})
        self._doc = self._sig.get ( "doc", "" )
        self._args = self._sig.get ( "args", {} )

    def message (self, **args):
        msg = { 'path' : self.path(), 'args' : args }
        return msg
        
    def isLeaf(self):
        return False
    
    def isLevel(self):
        return False

    def isFunction(self):
        return False

    def isVariable(self):
        return False
    
    def argnames(self):
        return self._args.keys()
    
    def isArgAccepted(self, arg):
        return False

    def path(self, stopat=None):
        if self._parent: 
            if self._parent.root or self._parent == stopat:
                return self.name
            else:
                return self._parent.path() + "." + self.name
        elif self.root:
            return ""
        else: 
            return self.name

    def hasChild(self, name):
        return name in self._children_idx        
        
    def addChild(self, childnode):
        childnode._parent = self
        if childnode not in self._children:
            self._children.append ( childnode )
            self._children_idx[childnode.name] = childnode
    
    def depth(self):
        if self._parent is None: return 0
        else: return 1 + self._parent.depth
        
    def __iter__(self):
        return iter(self._children)
    
    def printall(self):
        pref = "<node>"
        if self.isLevel(): pref = "[DIR]"
        elif self.isLeaf(): 
            if self.isFunction: pref = "[FN]"
            elif self.isVariable: pref = "[VAR]"
            else: pref = "[LEAF]"
            
        if len(self._children) > 0: cr = "\n"
        else: cr = ""
        return "{0:7}".format(pref) + self.path() + cr + "\n".join(map(lambda x: x.printall(), self._children))

    __repr__ = path
        
    def childrennames(self):
        return self._children_idx.keys()
    
    def __getitem__(self, key):
        return self._children_idx[key]
    
class CliLevel(CliNode):
    def __init__(self, name, **kkw):
        CliNode.__init__(self, name, **kkw)
    
    def isLevel(self):
        return True

class CliLeaf(CliNode):
    def __init__(self, name, **kkw):
        CliNode.__init__(self, name, **kkw)        
        
    def isLeaf(self):
        return True

class ParseError(Exception):
    pass
    
def CreateCliTree (signature):
    root = CliLevel ( "provcli" )
    def r_process_node ( sig, node ):
        for cmd in sig:
            if '__leaf__' not in sig[cmd]:
                lev = CliLevel ( cmd, parent=node )
                r_process_node ( sig[cmd], lev )
            else:
                leaf = CliLeaf ( cmd, parent=node, signature=sig[cmd] )                
    
    r_process_node ( signature, root )
    return root

def comand_line_parser (root, cl):
    current_node = root
    prev_dot = -1    
    space = False
    args = None
    prefix = None
    idx = 0
    for idx in range(0,len(cl)):
        char = cl[idx]
        if char in ['.', ' ']:
            levelname = cl[prev_dot+1:idx]
            if current_node.hasChild(levelname):
                current_node = current_node[levelname]
                prev_dot = idx
            else:
                raise ParseError ( levelname + " not found in " + current_node.path() )
        if char == ' ':
            space = True
            break
    if space:
        args = { 'complete' : [], 'begun' : None, 'space': True }
        argstart = idx+1
        valstart = 0
        inquote = False
        state = 1
        quotetype = None
        argname, argval = (False, False)
        for idx in range(idx+1, len(cl)):
            char = cl[idx]
            if char == '=':
                argname = cl[argstart:idx]
                valstart = idx+1
                state = 2
            if char == ' ':
                if state == 1:
                    raise ParseError ( "No value specified." )
                else:
                    argval = cl[valstart:idx]
                    args['complete'].append ( (argname, argval) )
                    argname, argval = (False, False)
                    state = 1
                    argstart = idx+1
        if argname and not argval:
            if valstart <= idx:
                args['complete'].append ( (argname, cl[valstart:]) )
            else:
                args['begun'] = argname
        elif not argname and argstart <= idx:
            args['begun'] = cl[argstart:]
        
    else:
        args = {'complete' : {}, 'begun' : None}
        levelname = cl[prev_dot+1:]
        if current_node.hasChild (levelname):
            current_node = current_node[levelname]
        else:
            prefix = levelname
            
    return (current_node, args, prefix)
    

def command_completer (text, state):        
    try:
        (level, args, prefix) = comand_line_parser ( currentLevel, text )
    except ParseError as perr:
        print perr
        return None

    if 'space' in args:
        keys = level.argnames()
    else:
        keys = level.childrennames()    
        if prefix: keys = filter ( lambda x: x.startswith(prefix), keys)
    
    if state < len(keys):
        if level != cliRoot and level != currentLevel:
            return level.path(stopat = currentLevel) + "." + keys[state]
        else:
            return keys[state]
    else:
        return None
    
signature = None
sigidx = {}

try:
    client = APP.CLIClient()
    signature = client.recv()
except socket.error:
    print "Connection failed."
    sys.exit(1)

cliRoot = CreateCliTree(signature)
cliRoot.root = True
print signature
print cliRoot.printall()


try:
    if hasReadline:
        readline.read_history_file ( os.path.expanduser("~/.prov-history") )
except IOError:
    pass
if hasReadline:
    atexit.register(readline.write_history_file, os.path.expanduser("~/.prov-history") )
    readline.parse_and_bind("tab: complete")
    readline.set_completer ( command_completer )
    readline.set_completer_delims("\n")

currentLevel = cliRoot

while True:
    try:        
        command = raw_input("(provcli) %s> " % currentLevel.path())

        if command.upper() in ["EXIT", "QUIT"]: break
        if command.upper() in ["HALT"]: 
            client.send ( "_SHUTDOWN" )
            break
        
        try:
            (level, args, prefix) = comand_line_parser ( currentLevel, command )
            print level.path(), args, prefix
            if isinstance(level, CliLevel) and prefix is None:
                currentLevel = level
            if isinstance(level, CliLeaf) and prefix is None:
                argsmap = {}
                for (an, av) in args['complete']: argsmap[an] = av
                client.send ( level.message ( ** argsmap ) )
                reply = client.recv()
                print reply
        except ParseError as perr:
            print perr
    except KeyboardInterrupt:        
        if currentLevel == cliRoot:
            break
        currentLevel = cliRoot
        print
    except EOFError:
        if currentLevel._parent is not None:
            currentLevel = currentLevel._parent
        else:
            break
        print
    except IOError:        
        print "Connection closed by peer."
        break
    

print
client.close()


