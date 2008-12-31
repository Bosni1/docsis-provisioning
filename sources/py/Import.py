##$Id$
import os

import pymssql, _mssql
import getpass
from ProvCon.dbui.database import CFG
import ProvCon.dbui.database as db
from ProvCon.dbui import meta, orm

if __name__=="__main__":
    #pw = getpass.getpass("Password for \\SQLEXPRESS\stansat:stansat@reklamy >")
    pw = "wajig05850_hax0r"
    stansatDB = pymssql.connect ( user = 'stansat', database = 'stansat', host = 'reklamy',
                                  password = pw )
    cr = stansatDB.cursor()
    print CFG.CX.query ( "DELETE FROM pv.city" )
    cr.execute ( "SELECT 'Index', Nazwa FROM Miejscowosc" )
    onMap = {}
    for mIndex, mNazwa in cr.fetchall():
        nRec = orm.Record.EMPTY ( "city" )
        nRec.name = mNazwa.decode("cp1250").encode('utf8')
        nRec.handle = ""
        nRec.write()
        onMap[mIndex] = nRec
    stansatDB.close()
    