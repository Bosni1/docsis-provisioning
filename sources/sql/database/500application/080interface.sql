-- $Id:$
create table {:SCHEMA:}mac_interface (  
  mac macaddr null,  
  designation smallint default 1,
  ipreservationid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  deviceid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  ownerid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  name varchar(32) null,
  type smallint not null default '1',  
  unique (mac, designation)
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'mac_interface' );
CREATE INDEX idx_mac_interface_mac on {:SCHEMA:}mac_interface (mac);

CREATE FUNCTION {:SCHEMA:}get_interface_mac (objid int8) returns macaddr AS $$
  DECLARE
    m varchar;    
  BEGIN
    SELECT mac INTO m 
    FROM {:SCHEMA:}mac_interface WHERE 
       objectid = objid
       LIMIT 1;    
    RETURN m;
  END;
$$ LANGUAGE plpgsql;

create function {:SCHEMA:}get_interface_first_ip(interfaceoid int8) returns inet AS $intip$ 
DECLARE
  ip inet;
BEGIN
  SELECT address INTO ip
  FROM {:SCHEMA:}ip_reservation i WHERE i.interfaceid = interfaceoid LIMIT 1;
  RETURN ip;
END;
$intip$ LANGUAGE plpgsql;

create function {:SCHEMA:}get_device_first_ip(deviceoid int8) returns inet AS $intip$ 
DECLARE
  ip inet;
BEGIN
  SELECT r.address INTO ip
  FROM {:SCHEMA:}ip_reservation r, {:SCHEMA:}mac_interface i WHERE r.interfaceid = i.objectid  AND 
    i.deviceid = deviceoid LIMIT 1;
  RETURN ip;
END;
$intip$ LANGUAGE plpgsql;

create function {:SCHEMA:}get_interface_reserved_ip(interfaceoid int8) returns inet AS $intip$ 
DECLARE
  ip inet;
BEGIN
  SELECT i.address INTO ip
  FROM {:SCHEMA:}ip_reservation i, {:SCHEMA:}mac_interface m WHERE m.ipreservationid = i.objectid 
     AND m.objectid = interfaceoid LIMIT 1;
  RETURN ip;
END;
$intip$ LANGUAGE plpgsql;
