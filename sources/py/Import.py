##$Id$
# -*- coding: utf8 -*-
import os
import pymssql, _mssql
import getpass
import MySQLdb
from ProvCon.dbui.database import CFG, Init
from ProvCon.dbui.di import rObject
Record = rObject
import atexit
import StringIO

def dictresult ( cr ):
    #assert isinstance( cr, pymssql.pymssqlCursor )
    result = []
    for r in cr.fetchall():
        rowresult = {}
        for desc, val in map(lambda x,y: (x,y), cr.description, r):
            rowresult[desc[0]] = val
        result.append(rowresult)
    return result

def close(db):
    print "EXIT"
    try:
        db.close()
    except:
        pass

def addObjectNote (obj, note, who=None):
    if isinstance (obj, orm.Record):
        objectid = obj.objectid
    else:
        objectid = obj
    note = orm.Record.EMPTY ( "note" )
    note.refobjectid = objectid
    note.who = who
    note.content = note
    note.write()

def setObjectFlag (obj, flagname):    
    if isinstance (obj, orm.Record):
        objectid = obj.objectid
    else:
        objectid = obj
    flag = orm.Record.EMPTY ( "object_flag" )
    flag.refobjectid = objectid
    flag.flagname = flagname
    flag.write()
    
    
if __name__=="__main__":
    DataErrors = StringIO.StringIO()
    
    #połączenie z bazą docsis-provisioning
    Init()    
        
    #polaczenie z SQLEXPRESS - bazą biurową
    #pw = getpass.getpass("Password for \\SQLEXPRESS\stansat:stansat@reklamy >")
    pw = "wajig05850_hax0r"
    stansatDB = pymssql.connect ( user = 'stansat', database = 'stansat', host = 'reklamy',
                                  password = pw )
    cr = stansatDB.cursor()
    atexit.register ( close, stansatDB )
    
    #połączenie z bazą NetCon 2.0
    n2db = MySQLdb.connect ( db='techdb', user='netcon3', host='83.243.39.5', charset='utf8' )
    n2cr = n2db.cursor()
    
    #Pobieranie danych z NetCon 2.0
    n2cr.execute ( "SELECT * FROM customer" )
    #Pobieramy dane o klientach (tabela 'customer'), i indeksujemy po
    # - id  ( id w bazie netcona == skrót w bazie biurowej )
    # - nazwie
    n2_customer_all = dictresult (n2cr)
    n2_customer_idMap = {}
    n2_customer_nameMap = {}
    for c in n2_customer_all:        
        #znacznik, czy ten rekord był już importowany
        c['_imported'] = False
        #przypisany numer klienta z bazy biurowej        
        c['_subscriberid'] = None
        c['_devices'] = []
        c['_n3'] = None
        c['IP'] = []    #adresy ip z netcona
        c['MAC'] = []   #adresy mac z netcona
        n2_customer_idMap[c['id']] = c
        n2_customer_nameMap[c['name']] = c
    
    #wypełniamy adresy ip
    n2cr.execute ( "SELECT *, int2ipstr(ip) as ipaddr FROM customer_ip_assignment" )
    n2_ip_all = dictresult(n2cr)    
    for i in n2_ip_all:
        n2_customer_idMap[i['customer']]['IP'].append (i)
    
    #wypełniamy adresy MAC
    n2cr.execute ( "SELECT *, int2ipstr(dhcp_ip) as ipaddr FROM customer_known_mac" )
    n2_mac_all = dictresult(n2cr)    
    for i in n2_mac_all:
        n2_customer_idMap[i['customer']]['MAC'].append (i)
    
    n2cr.execute ( "SELECT * FROM ip_device")
    n2_device_all = dictresult(n2cr)
    device_models_map = {}
    for device_row in n2_device_all:
        device_row['_interfaces'] = []
        device_row['_ip'] = []
        device_row['_routes'] = []
        device_row['_customers'] = []
        device_row['__objectid'] = None
        device_models_map[device_row['model']] = None
        
    n2_device_idMap = {}
    map (lambda r: n2_device_idMap.update ( { r['id'] : r } ), n2_device_all )
    
    n2cr.execute ( "SELECT * FROM ip_device_interface" )
    n2_interface_all = dictresult(n2cr)    
    n2_interface_idMap = {}
    map (lambda r: n2_interface_idMap.update ( { r['id'] : r }), n2_interface_all )
             
    for info_table in ["br_port", "cm", "cmts_ds", "cmts_us", "radio"]:
        n2cr.execute ( "SELECT * FROM ip_device_interface_" + info_table )
        data = dictresult(n2cr)
        for info_row in data:
            interface_row = n2_interface_idMap[info_row['interface']]
            interface_row[info_table] = info_row
            if info_table == "br_port": interface_row["br_port"] = data
            
    for interface_row in n2_interface_all:
        interface_row['_ip'] = []
        interface_row['_n3'] = None
        n2_device_idMap[interface_row['device']]['_interfaces'].append ( interface_row )        
    
    n2cr.execute( "SELECT *, int2ipstr(ip) as ipstr FROM ip_device_interface_ip_assignment" )
    n2_interface_ip = dictresult(n2cr)
    for ip_row in n2_interface_ip:
        interface_row = n2_interface_idMap[ip_row['interface']]
        interface_row['_ip'].append ( ip_row )
        n2_device_idMap[interface_row['device']]['_ip'].append ( ip_row )
        
    n2cr.execute ( "SELECT * FROM customer_ip_device" )
    n2_customer_device = dictresult(n2cr)                            
    map (lambda r: n2_customer_idMap[r['customer']]['_devices'].append ( n2_device_idMap[r['device']] ), n2_customer_device)
    map (lambda r: n2_device_idMap[r['device']]['_customers'].append ( n2_customer_idMap[r['customer']] ), n2_customer_device)    

    n2cr.execute ( "SELECT * FROM class_of_service" )
    n2_cos_all = dictresult(n2cr)
    n2_cos_idMap = {}
    map (lambda r: n2_cos_idMap.update ({ r['id'] : r } ), n2_cos_all )

    n2cr.execute ( "SELECT *, int2ipstr(network) as netstr, int2ipstr(default_router) as gateway FROM ip_address_space" )
    n2_subnet_all = dictresult(n2cr)
    
    n_TOS = {}   #hash z typami usługi
    n_COS = {}   #hash z pakietami
    n2o_intMap = {}
    n2o_tvMap = {}
    o_pakietIntIdx = {}  #??
    p_pakietTVIdx = {}   #??

    CFG.CX.query ( "DELETE FROM {0}.subscriber".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.service".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.device".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.device_role".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.ip_reservation".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.ip_subnet".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.ip_subnet_group".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.mac_interface".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.class_of_service".format(CFG.DB.SCHEMA) )
    CFG.CX.query ( "DELETE FROM {0}.type_of_service".format(CFG.DB.SCHEMA) )

    #Podsieci IP
    mainSubnetGroupRec = Record ( "ip_subnet_group" )
    mainSubnetGroupRec.name = "Wszystkie adresy IP"
    mainSubnetGroupRec.write()

    for subnet in n2_subnet_all:
        subRec = Record ( "ip_subnet" )
        subRec.subnetgroupid = mainSubnetGroupRec.objectid
        subRec.name = subnet["name"]
        if subnet["address_type"] == "CUST":
            subRec.designation = [1]
            subRec.scope = "SUBSCRIBER"
        elif subnet["address_type"] == "EQUI":
            subRec.designation = [2]
            subRec.scope = "MANAGEMENT"
        elif subnet["address_type"] == "CM":
            subRec.designation = [3]
            subRec.scope = "DOCSIS"
        subRec.network = subnet["netstr"]
        subRec.gateway = subnet["gateway"]
        subRec.active = subnet["active"]
        subRec.allownew = subnet["new_allowed"]
        subRec.dhcpserver = "10.1.0.2"
        subRec.write()
        
    
    #Modele urządzeń
    for m in device_models_map.keys():
        mRec = Record ( "device_model" )
        mRec.name = m
        mRec.write()
        device_models_map[m] = mRec
    
    #Urządzenia
    for device in n2_device_all:
        dRec = Record ( "device" )
        dRec.name = device['name']                
        dRec.devicerole = []
        dRec.devicelevel = '?'
        dRec.serialnumber = device["serial_number"]
        dRec.modelid = device_models_map[device['model']].objectid                    
        dRec.write()
        deviceroles = set()
        device["_n3"] = dRec
        for interface in device["_interfaces"]:
            iRec = Record ( "mac_interface")
            iRec.name = interface["name"]
            iRec.mac = interface["mac"]
            iRec.designation = 2
            iRec.deviceid = dRec.objectid            
            iRec.ownerid = dRec.objectid
            iRec.write()
            
            if "cm" in interface:
                cm = interface["cm"]
                cmRec = Record ( "docsis_cable_modem" )
                cmRec.deviceid = dRec.objectid
                cmRec.hfcmacid = iRec.objectid
                cmRec.customersn = device["serial_number"]                
                cmRec.maxcpe = cm["max_cpe"]
                if cm['docsis11']:
                    cmRec.docsisversion = 1.1
                cmRec.nightsurf = cm['nightsurf']
                cmRec.networkaccess = cm['active']
                cmRec.vendor = cm['VENDOR']
                cmRec.hw_rev = cm['HW_REV']
                cmRec.sw_rev = cm['SW_REV']
                cmRec.model = cm['MODEL']
                cmRec.bootr = cm['BOOTR']
                cmRec.basecap = cm['BASECAP']
                deviceroles.add ( "docsis_cable_modem" )
                cmRec.write()                
            elif "radio" in interface:
                radio = interface["radio"]
                if radio["mode"] == "APC" or radio["mode"] is None:
                    apcRec = Record ( "wireless_client" )
                    apcRec.deviceid = dRec.objectid
                    apcRec.interfaceid = iRec.objectid
                    deviceroles.add ( "wireless_client" )
                    apcRec.write()
                elif radio["mode"] == "AP":
                    apRec = Record ( "wireless_ap" )
                    apRec.deviceid = dRec.objectid
                    apRec.interfaceid = iRec.objectid
                    apRec.essid = radio["essid"]
                    deviceroles.add ( "wireless_ap" )
                    apRec.write()
                else:
                    wir = Record ( "wireless" )
                    wir.deviceid = dRec.objectid
                    wir.interfaceid = iRec.objectid
                    deviceroles.add ( "wireless" )
                    wir.write()            
            elif "br_port" in interface:
                br = interface["br_port"]
                brRec = Record ( "core_switch" )
                
            for ip in interface['_ip']:
                ipRec = Record ( "ip_reservation" )
                ipRec.interfaceid = iRec.objectid
                ipRec.address = ip["ipstr"]
                ipRec.designation = 2
                ipRec.state = 1                                
                ipRec.write()
            
        if device["type"] == 'ROUTER':
            natRec = Record ( "nat_router" )
            natRec.deviceid = dRec.objectid            
            natRec.localaddr = '192.168.2.1/24'
            natRec.lanports = 5
            deviceroles.add ( "nat_router" )
            natRec.write ()

        dRec.devicerole = list(deviceroles)
        dRec.write()
        
    
    #Import pakietów dostępu do Internetu
    cr.execute ("SELECT * FROM PakietInternet")
    
    pakiet_all = dictresult (cr)
    pakiet_IdxMap = {}   #pakiety (class_of_service) w nowej bazie indeksowane
                         #wg pola 'Index' w bazie biurowej                         

    #na razie dodajemy jeden typ usługi - Internet
    #TODO: dodać inne typy usługi
    tosRec = Record.EMPTY ( "type_of_service" )
    tosRec.typeid = "INT"
    tosRec.name = "Internet"
    tosRec.official_name = "Dostęp do Internetu"
    tosRec.classmap = []
    tosRec.write()
    
    cosIdx = [] 
    for p in pakiet_all:
        pRec = Record.EMPTY ( "class_of_service" )
        pRec.classid = p["Index"]
        pRec.name = p["Nazwa"].decode("cp1250")
        pRec.official_name = pRec.name
        pRec.write()
        cosIdx.append ( pRec.objectid )
        pakiet_IdxMap[p["Index"]] = pRec
    tosRec.classmap = cosIdx
    tosRec.write()
    
    
    cr.execute ( "SELECT TOP 10000 * FROM Klient" )
    klient_all = dictresult ( cr )
    cr.execute ( "SELECT * FROM DaneKlientInternet" )
    dki_all = dictresult ( cr )
    dki_IdxMap = {}
    for dki in dki_all:
        dki_IdxMap[dki["KlientIndex"]] = dki

    #cr.execute ( "SELECT * FROM DaneKlientTelewizja" )
    #dkt_all = dictresult ( cr )
    
    
    #hash nowych rekordów, indeksowany polem 'Index' z bazy biurowej (subscriberid)
    subscriber_oldIdxMap = {}    
    #tworzymy rekordy subscriber
    for K in klient_all:        
        subRec = Record ( "subscriber" )
        subRec.subscriberid = K["Index"]        
        subRec.name = ( (K["Imie"] or "") + " " + (K["Nazwisko"] or "")).strip().decode ( "cp1250" ).encode('utf8')
        subRec.postaladdress = (K["AdresKorespondencji"] or "").decode("cp1250").strip()
        if len(subRec.postaladdress) == 0: subRec.postaladdress = None
        if K["EMail"]:
            subRec.email = [ K["EMail"].decode("cp1250").encode("utf8") ]
        subRec.telephone = []
        if K["TelefonStacjonarny"]: subRec.telephone.append ( K["TelefonStacjonarny"][:32].decode("cp1250").encode("utf8") )
        if K["TelefonKomorkowy"]: subRec.telephone.append ( K["TelefonKomorkowy"][:32].decode("cp1250").encode("utf8") )
        subRec.write()        
        if K["OdbiorFaktur"]: subRec.PARAM.ODBIOR_FAKTUR = K["OdbiorFaktur"]
        if K["Wyszukiwanie"]: subRec.PARAM.SEARCH_EXPRESSION = K["Wyszukiwanie"].decode ( "cp1250" )
        if K["wynajmuje"]: subRec.FLAGS.WYNAJMUJE = True
        if K["Koperta"]: subRec.FLAGS.KOPERTA = True
        if K["BrakZgodyNaPrzetwarzanieDanych"]: subRec.FLAGS.BRAK_ZGODY_PD = True
        skrot = K["Skrot"].decode("cp1250").encode('utf8')
        #stary skrót z bazy biurowej zapamiętujemy jako parametr SKROT
        subRec.PARAM.SKROT = K["Skrot"].decode("cp1250")
        subscriber_oldIdxMap[K["Index"]] = subRec
            
        
    #Tworzymy lokalizacje        
    #Miejscowości (city)   
    CFG.CX.query ( "DELETE FROM {0}.city".format(CFG.DB.SCHEMA) )
    cr.execute ( "SELECT [Index], Nazwa FROM Miejscowosc" )
    #nowe rekordy 'city' indeksowane po:
    city_onMap = {}     #'Index' z bazy biurowej
    city_nameMap = {}   #'Nazwa' z bazy biurowej
    for mIndex, mNazwa in cr.fetchall():        
        nRec = Record.EMPTY ( "city" )
        cityName = mNazwa.decode("cp1250")
        
        #W bazie biurowej nazwy miast się dublują, więc jeśli miasto o tej
        #nazwie już jest wczytane - przyporządkowujemy mu już istniejący nowy
        #rekord
        if cityName in city_nameMap:
            city_onMap[mIndex] = city_nameMap[cityName]        
            continue
        
        nRec.name = cityName
        nRec.handle = None
        try:
            nRec.write()
        except Record.DataManipulationError, e:
            print str(e)
        city_onMap[mIndex] = nRec
        city_nameMap[cityName] = nRec

    #Ulice
    cr.execute ( "SELECT [Index], Nazwa, Skrot FROM Ulica" )
    #Na razie tylko budujemy ten hash, 'Index' -> (nazwa,skrot), ponieważ w bazie biurowej ulice
    #nie są powiązane z miejscowościami czasami jedna ulica występuje w wielu.
    ulica_idMap = {}
    for uIndex, uNazwa, uSkrot in cr.fetchall():
        ulica_idMap[uIndex] = (uNazwa, uSkrot or "")
    
    #Reszta danych o lokalizacjach w bazie biurowej jest w tabeli Klient, więc przechodzimy po wszystkich
    #klientach i tworzymy budynki i lokale (building i location)
    cr.execute ( "SELECT [Index], Skrot, UlicaIndex, MiejscowoscIndex, NrDomu, NrMieszkania, KodPocztowy FROM Klient" )

    klient_localizationMap = {} #lokalizacje indeksowane po 'Index' klienta z bazy biurowej
    city_street_objMap = {}     #już stworzone rekordy 'street' powiązane z miastem
    building_objMap = {}        #[street objectid][nr domu] = nowy rekord building
    location_objMap = {}        #[building objectid][nr lokalu] = nowy rekord location
    
    for kIndex, kSkrot, uIndex, mIndex, kNrDomu, kNrMieszkania, kKodPocztowy in cr.fetchall():
        if not (mIndex, uIndex) in city_street_objMap:
            #jeśli ulica jeszcze nie została dodana
            uRec = Record.EMPTY ( "street" )
            try:
                name, handle = ulica_idMap[uIndex]
            except KeyError:
                #jeżeli nie ma takiego UlicaIndex, to coś jest w bazie pojebane,
                #albo po prostu pole nie zostało ustawione
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
            bRec = Record.EMPTY ( "building" )
            if kNrDomu is None:
                #to jest dziwne, ale cóż...
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
            lRec = Record.EMPTY ( "location" )
            if kNrMieszkania == "NULL": kNrMieszkania = None
            lRec.number = kNrMieszkania
            lRec.buildingid = bRec.objectid
            lRec.write()
            location_objMap[bRec.objectid][kNrMieszkania] = lRec
        else:
            lRec = location_objMap[bRec.objectid][kNrMieszkania]

        klient_localizationMap[kIndex] = lRec
    
    #Teraz przypisujemy primarylocationid do klienta:
    for kIndex in subscriber_oldIdxMap:
        subRec = subscriber_oldIdxMap[kIndex]
        try:
            subRec.primarylocationid = klient_localizationMap[kIndex].objectid
            if klient_localizationMap[kIndex].number == "NULL":
                klient_localizationMap[kIndex].number = None
                klient_localizationMap[kIndex].write()                
        except KeyError:
            pass
        subRec.write()

        
        
    #Dodajemy usługi, adresy IP i MAC, urządzenia klienckie
    for K in klient_all:
        dki = dki_IdxMap[K["Index"]]
        skrot = K["Skrot"].decode('cp1250').encode('utf8')
        
        subRec = subscriber_oldIdxMap[K["Index"]]
        
        srvRec = Record ( "service" )
        srvRec.subscriberid = subRec.objectid

        try:
            srvRec.classofservice = pakiet_IdxMap[dki["PakietIndex"]].objectid
        except KeyError:
            #DataErrors.write ( " 'PakietIndex' = '{0}' (klient: {1}), nie znaleziony pakiet.\n".format (dki["PakietIndex"], skrot) )
            print "Service DKI key not found."
            continue
        
        srvRec.typeofservice = tosRec.objectid
        srvRec.locationid = klient_localizationMap[K["Index"]].objectid        
        srvRec.write()
        
        n2c = None
        
        if skrot in n2_customer_idMap:
            n2c = n2_customer_idMap[skrot]
        elif subRec.name in n2_customer_nameMap:
            n2c = n2_customer_nameMap[subRec.name]
            DataErrors.write ("Data Error: Klient skrót: {0} nie został znaleziony w bazie N2, ale nazwa={1} tak.\n".format (skrot, subRec.name)  )
            continue
        
        if n2c is None:
            #DataErrors.write( "Data Error: Klient %s [%s] #%d nie znaleziony w bazie N2\n" % (skrot, subRec.name, subRec.subscriberid))
            continue        

        n2c['_n3'] = subRec
        
        try:
            ip_id_map = {}
            for ip in n2c['IP']:
                iprRec = Record ( "ip_reservation" )
                iprRec.ownerid = srvRec.objectid
                iprRec.address = ip['ipaddr']                
                iprRec.write()
                ip_id_map[ip['ipaddr']] = iprRec.objectid
            
            for idx, mac in enumerate(n2c['MAC']):
                macRec = Record ( "mac_interface" )
                macRec.designation = 1
                macRec.ownerid = srvRec.objectid
                macRec.mac = mac['mac']
            
                devRec = Record( "device" )
                
                devRec.devicelevel = "CPE"
                devRec.devicerole = ["cpe"]
                devRec.write()
                
                cpeRec = Record ( "cpe" )
                cpeRec.deviceid = devRec.objectid
                cpeRec.name = "#{0}".format (idx+1)                                                
                
                if mac['ipaddr'] is not None:
                    try:
                        macRec.ipreservationid = ip_id_map[mac['ipaddr']]
                    except KeyError:
                        DataErrors.write ( "!!!!!!! MAC: %s (%s) ma przypisany nieznany adres IP.\n" % (mac['mac'], mac['customer']) )
                        pass
                macRec.write()                                        
                cpeRec.macid = macRec.objectid
                cpeRec.write()
                
                srvRec.related_device = devRec.objectid

            for device in n2c["_devices"]:
                dRec = device["_n3"]
                srvRec.related_device = dRec.objectid
            
        except Record.DataManipulationError, e:
            DataErrors.write ( str(e) )            
        except KeyError:
            pass
        
    print "#" * 80
    print "## DATA ERRORS ##"
    print DataErrors.getvalue()
            
            


    
    stansatDB.close()
    

    