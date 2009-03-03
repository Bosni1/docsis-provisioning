create table {:SCHEMA:}device (
  name varchar(128) null,
  parentid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  ownerid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  devicelevel varchar(4) not null,
  devicerole varchar(64)[] null,
  modelid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  serialnumber varchar(128) null
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'device' );

create table {:SCHEMA:}device_model (
  name varchar(128) null,
  defaultroles varchar(64)[] null,
  info text
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'device_model' );


CREATE FUNCTION {:SCHEMA:}get_device_text (objid int8) returns text AS $$
  DECLARE
    dev RECORD;
    txt text;
    cnt integer;
  BEGIN
    SELECT d.*, m.name as modelname INTO dev FROM {:SCHEMA:}device d LEFT JOIN {:SCHEMA:}device_model m ON m.objectid = d.modelid WHERE d.objectid = objid LIMIT 1;
    GET DIAGNOSTICS cnt = ROW_COUNT;

    IF cnt = 0 THEN
       RETURN NULL;
    END IF;

    IF 'docsis_cable_modem' = ANY ( dev.devicerole ) THEN 
       txt := 'MODEM KABLOWY';
       IF 'sip_client' = ANY ( dev.devicerole ) THEN
          txt := txt || ' (MTA)';
       END IF;
       IF 'nat_router' = ANY ( dev.devicerole ) THEN
          txt := txt || ' z ROUTEREM';
       END IF;
       IF 'wireless_ap' = ANY ( dev.devicerole ) THEN
          txt := txt || ' z WiFi';
       END IF;
    ELSIF 'cpe' = ANY ( dev.devicerole ) THEN
       IF 'wireless_client' = ANY ( dev.devicerole ) THEN
          txt := 'KARTA BEZPRZEWODOWA';
       ELSE
          txt := 'KARTA SIECIOWA';
       END IF;
    ELSIF 'sip_client' = ANY ( dev.devicerole ) THEN
       txt := 'Bramka VoIP';
    ELSIF 'nat_router' = ANY ( dev.devicerole ) THEN
       IF 'wireless_ap' = ANY ( dev.devicerole ) THEN
           txt := 'ROUTER z WiFi';
       ELSE 
           txt := 'ROUTER';
       END IF;
    ELSE    
       txt := dev.name || ' ' || dev.devicerole::text;
    END IF;
    txt := txt || ' ' || coalesce(dev.modelname,'');
    RETURN txt;
  END;
$$ LANGUAGE plpgsql;
