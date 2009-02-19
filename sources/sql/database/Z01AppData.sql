--COPY pv.type_of_service (typeid, name,classmap,info) FROM STDIN DELIMITER '|';
--I/K|Internet / TVK|{}|Dostęp do Internetu w sieci telewizji kablowej
--I/R|Internet / Radio|{}|Dostęp do Internetu przez łącze radiowe
--I/L|Internet / LAN|{}|Dostęp do Internetu w sieci LAN
--I/AV|Antywirus|{}|Pakiet antywirusowy GDATA
--I/FW|Firewall|{}|Ochrona komputera GDATA
--I/IP|Dodatkowy IP|{}|Konfiguracja dla dodatkowego komputera
--I/WL|Wireless|{}|Bezprzewodowy Internet w domu
--\.

CREATE FUNCTION T(tid varchar) returns int8  as $$
    DECLARE 
        obid int8;
    BEGIN
        SELECT objectid INTO obid FROM pv.type_of_service WHERE typeid = tid;
        RETURN obid;
    END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION C(tid varchar) returns int8  as $$
    DECLARE 
        obid int8;
    BEGIN
        SELECT objectid INTO obid FROM pv.class_of_service WHERE classid = tid;
        RETURN obid;
    END;
$$ LANGUAGE plpgsql;

--INSERT INTO pv.class_of_service (classid, name) VALUES ( 'INT/B', 'Biały');
--INSERT INTO pv.class_of_service (classid, name) VALUES ( 'INT/M', 'Niebieski');
--INSERT INTO pv.class_of_service (classid, name) VALUES ( 'INT/N', 'Średni');
--INSERT INTO pv.class_of_service (classid, name) VALUES ( 'INT/D', 'Złoty');

DROP FUNCTION T(varchar);
DROP FUNCTION C(varchar);

