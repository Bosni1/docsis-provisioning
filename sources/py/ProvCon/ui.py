#!/bin/env python
import ProvCon

__all__ = [ "signature", "action" ]

_UI_SIGNATURE_ = {}
_UI_SIGNATURE_IDX_ = {}
_UI_ACTIONS_ = {}
_UI_ACTIONS_IDX_ = {}


def signature():
    return _UI_SIGNATURE_


class uierror(Exception):
    def __init__(self, path, exname, exval, esource = None):
        Exception.__init__(self)
        self.path = path
        self.exname = exname
        self.exval = exval
        self.esource = esource
    
    def __repr__(self):
        return "ui error ({path}): {exname} '{exval}' @ {esource}".format ( **self.__dict__)

def ui ( *path, **options ):
    def decorator(f):        
        fullpath = ".".join( list(path) )
        def ui_action(**kkw):
            try:
                response = f(**kkw)
            except Exception as e:
                raise uierror ( fullpath, "Unhandled system error: " + e.__class__.__name__, 
                                e.message, '??' )
            return response
                
        current_sig = _UI_SIGNATURE_
        current_act = _UI_ACTIONS_
        for level in list(path)[:-1]:            
            if level not in current_sig: current_sig[level] = {}
            if level not in current_act: current_act[level] = {}
            current_sig = current_sig[level]
            current_act = current_act[level]
        leaf = list(path)[-1]
        leaftype = options.get ( "type", UI_FUNCTION )
        leafargs = options.get ( "args", {} )
        current_sig[leaf] = { 
            '__leaf__' : True,
            'type' : leaftype, 
            'valuetype' : options.get ( "valuetype", "text" ),
            'doc' : f.__doc__, 
            'args' : leafargs
            }
        current_act[leaf] = (ui_action, leaftype)
        _UI_SIGNATURE_IDX_[fullpath] = current_sig[leaf]
        _UI_ACTIONS_IDX_[fullpath] = current_act[leaf]
        return ui_action
    
    return decorator

UI_FUNCTION = 1
UI_VARIABLE = 2

def action ( path, context, **kkw ):
    if type(path) is str: fullpath = path
    elif type(path) in [tuple, list]: fullpath = ".".join ( list(path) )
    else:
        raise uierror ( "execute_action: " + str(type(path)), "Invalid argument", 
                        "Argument 'path' is not of an accepted type" )

    (action_fn, leaftype) = _UI_ACTIONS_IDX_[fullpath]
    return action_fn ( __context = context, **kkw )

@ui("system", "status", 
    type=UI_FUNCTION)
def system_status (**kkw):
    """Check the current status of all Provisioning tasks."""
    return "OK"

@ui("service", "controller", type=UI_FUNCTION,
    args= { 'name' : 'service name', 'action' : 'action to perform' }
    )
def service_controller (**kkw):
    return "OK"
    

@ui("test", "one", "two")
def test(**kkw):
    return "AAA"

#partial UI controller ( tftpd, data_proxy, .... ) ???

