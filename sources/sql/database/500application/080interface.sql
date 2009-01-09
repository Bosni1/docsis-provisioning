-- $Id:$
create table {:SCHEMA:}mac_interface (
  mac macaddr not null unique,
  ipreservationid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'mac_interface' );