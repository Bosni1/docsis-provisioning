##$Id$
# -*- coding: utf8 -*-
import os
import pymssql, _mssql
import getpass
from ProvCon.dbui.database import CFG
import ProvCon.dbui.database as db
from ProvCon.dbui import meta, orm
import atexit

def dictresult ( cr ):
    assert isinstance( cr, pymssql.pymssqlCursor )
    result = []
    for r in cr.fetchall():
        rowresult = {}
        for desc, val in map(lambda x,y: (x,y), cr.description, r):
            rowresult[desc[0]] = val
        result.append(rowresult)
    return result

def close(db):
    db.close()
    
if __name__=="__main__":
    #pw = getpass.getpass("Password for \\SQLEXPRESS\stansat:stansat@reklamy >")
    pw = "wajig05850_hax0r"
    stansatDB = pymssql.connect ( user = 'stansat', database = 'stansat', host = 'reklamy',
                                  password = pw )
    cr = stansatDB.cursor()

    atexit.register ( close, stansatDB )
    
    cr.execute ( "SELECT * FROM Klient" )
    klient_all = dictresult ( cr )
    cr.execute ( "SELECT * FROM DaneKlientInternet" )
    dki_all = dictresult ( cr )
    cr.execute ( "SELECT * FROM DaneKlientTelewizja" )
    dkt_all = dictresult ( cr )

    CFG.CX.query ( "DELETE FROM pv.subscriber" )
    
    for K in klient_all:        
        subRec = orm.Record.EMPTY ( "subscriber" )
        subRec.subscriberid = K["Index"]        
        subRec.name = ( (K["Imie"] or "") + " " + (K["Nazwisko"] or "")).strip().decode ( "cp1250" )
        subRec.postaladdress = (K["AdresKorespondencji"] or "").decode("cp1250")        
        if K["EMail"]:
            subRec.email = [ K["EMail"].decode("cp1250").encode("utf8") ]
        subRec.telephone = []
        if K["TelefonStacjonarny"]: subRec.telephone.append ( K["TelefonStacjonarny"][:32].decode("cp1250").encode("utf8") )
        if K["TelefonKomorkowy"]: subRec.telephone.append ( K["TelefonKomorkowy"][:32].decode("cp1250").encode("utf8") )        
        subRec.write()
    
    #Miejscowości    
    CFG.CX.query ( "DELETE FROM pv.city" )
    cr.execute ( "SELECT [Index], Nazwa FROM Miejscowosc" )
    city_onMap = {}
    city_nameMap = {}
    for mIndex, mNazwa in cr.fetchall():
        nRec = orm.Record.EMPTY ( "city" )
        cityName = mNazwa.decode("cp1250")

        if cityName in city_nameMap:
            city_onMap[mIndex] = city_nameMap[cityName]        
            continue
            
        nRec.name = cityName
        nRec.handle = ""
        try:
            nRec.write()
        except orm.record.Record.DataManipulationError, e:
            print str(e)
        city_onMap[mIndex] = nRec
        city_nameMap[cityName] = nRec

    #Ulice
    cr.execute ( "SELECT [Index], Nazwa, Skrot FROM Ulica" )
    ulica_idMap = {}
    for uIndex, uNazwa, uSkrot in cr.fetchall():
        ulica_idMap[uIndex] = (uNazwa, uSkrot)
    
    cr.execute ( "SELECT [Index], Skrot, UlicaIndex, MiejscowoscIndex, NrDomu, NrMieszkania, KodPocztowy FROM Klient" )

    klient_localizationMap = {}
    city_street_objMap = {}
    building_objMap = {}
    location_objMap = {}
    klient_objMap = {}
    
    for kIndex, kSkrot, uIndex, mIndex, kNrDomu, kNrMieszkania, kKodPocztowy in cr.fetchall():
        if not (mIndex, uIndex) in city_street_objMap:
            uRec = orm.Record.EMPTY ( "street" )
            try:
                name, handle = ulica_idMap[uIndex]
            except KeyError:
                print kIndex, kSkrot, "incomplete location data."
                continue
            uRec.name = name.decode("cp1250")
            uRec.handle = handle
            uRec.cityid = city_onMap[mIndex].objectid
            uRec.write()
            city_street_objMap[ (mIndex, uIndex) ] = uRec
        else:
            uRec = city_street_objMap[ (mIndex, uIndex) ] 
        
        if not uRec.objectid in building_objMap:
            building_objMap[uRec.objectid] = {}
        
        if not kNrDomu in building_objMap[uRec.objectid]:
            bRec = orm.Record.EMPTY ( "building" )
            if kNrDomu is None:
                bRec.number = "<brak>"
            else:
                bRec.number = kNrDomu.decode ( "cp1250" )
            bRec.streetid = uRec.objectid
            bRec.postal_code = kKodPocztowy
            bRec.write()
            building_objMap[uRec.objectid][kNrDomu] = bRec
        else:
            bRec = building_objMap[uRec.objectid][kNrDomu]
            
        if not bRec.objectid in location_objMap:
            location_objMap[bRec.objectid] = {}
            
        if not kNrMieszkania  in location_objMap[bRec.objectid]:
            lRec = orm.Record.EMPTY ( "location" )
            lRec.number = kNrMieszkania
            lRec.buildingid = bRec.objectid
            lRec.write()
            location_objMap[bRec.objectid][kNrMieszkania] = lRec
        else:
            lRec = location_objMap[bRec.objectid][kNrMieszkania]

        klient_localizationMap[kIndex] = lRec

        
    stansatDB.close()
    

    