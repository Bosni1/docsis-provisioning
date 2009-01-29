# -*- coding: utf8 -*-

def ExportMetaData ( filename ):
    from ProvCon.dbui.database import CFG
    import cPickle
    ti_rs = CFG.CX.query ( "SELECT * FROM {0}.table_info".format (CFG.DB.SCHEMA) ).dictresult()
    fi_rs = CFG.CX.query ( "SELECT * FROM {0}.field_info".format (CFG.DB.SCHEMA) ).dictresult()
    mtm_rs = CFG.CX.query ( "SELECT * FROM {0}.mtm_relationship".format (CFG.DB.SCHEMA) ).dictresult()
    export = { 'table' : ti_rs, 'field' : fi_rs, 'mtm' : mtm_rs }        
    
    with open(filename, 'w') as f:
        cPickle.dump (export, f)
    


def ImportMetaData ( filename ):
    from ProvCon.dbui.database import CFG
    from ProvCon.dbui import orm
    import cPickle

    export = cPickle.load ( open (filename, 'r') )
    
    yield "Ładowanie aktualnych ustawień."
    
    current_ti = CFG.CX.query ( "SELECT objectid, schema || '.' || name as path FROM {0}.table_info".format(CFG.DB.SCHEMA) ).dictresult()
    current_fi = CFG.CX.query ( "SELECT objectid, classid as parent, path FROM {0}.field_info".format(CFG.DB.SCHEMA) ).dictresult()

    cTI = {}
    cFI = {}
    for t in current_ti: cTI[t['path']] = t['objectid']
    for f in current_fi: cFI[f['path']] = f['objectid']

    oTI = {}
    oFI = {}            
    o_idTI = {}
    o_idFI = {}            

    ti = export['table']
    fi = export['field']
    
    for t in ti: 
        o_idTI[t['objectid']] = t
        oTI[t['schema'] + "." + t['name']] = t
        
    for f in fi: 
        o_idFI[t['objectid']] = f
        oFI[f['path']] = f
        
    cTable = orm.Record.EMPTY("table_info")
    cField = orm.Record.EMPTY("field_info")
    
    direct_copy = [ "label", "title", "info", "pprint_expression",
                    "disabledfields", "recordlistpopup",
                    "knownflags", "knownparams","hasevents",
                    "hasnotes","excludedfields", 
                    "txtexpression", "recordlisttoolbox" ]   
    
    for t in cTI:
        yield t
        try:
            ot = oTI[t]
        except KeyError:
            continue
        cTable.setObjectID ( cTI[t] )
        
        for cn in direct_copy:                    
            fld = cTable._table[cn]
            val = ot[cn]
            if fld.isarray: 
                if val: val = "array:" + val
                else: val = '' 
                val = fld.val_txt2py(val)                    
            print cn, val
            cTable.setFieldValue(cn, val)
                
        cTable.write()   
    
    direct_copy = [ "label", "length", "choices", "ndims",
                        "reference_editable", "pprint_fkexpression",
                        "required", "protected", "nullable",
                        "quickhelp", "helptopic", "info",
                        "editor_class", "editor_class_params" ]

    for f in cFI:                
        try:
            of = oFI[f]
        except KeyError:
            continue
        yield f
        cField.setObjectID (cFI[f])
        
        for cn in direct_copy:                    
            fld = cField._table[cn]                    
            val = of[cn]
            if fld.isarray: 
                if val: val = "array:" + val
                else: val = '' 
                val = fld.val_txt2py(val)                    
            cField.setFieldValue(cn, val)
        
        if of["arrayof"]:    
            oldt = o_idTI [ of["arrayof"] ]
            oldtpath = oldt["schema"] + "." + oldt["name"]
            cField.arrayof = cTI[ oldtpath ]                                                        

        cField.write()
 