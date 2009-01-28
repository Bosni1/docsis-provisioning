-- $Id:$
create table {:SCHEMA:}mac_interface (
  mac macaddr not null,
  designation int default 0,
  ipreservationid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  ownerid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  unique (mac, designation)
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'mac_interface' );