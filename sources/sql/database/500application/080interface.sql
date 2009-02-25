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