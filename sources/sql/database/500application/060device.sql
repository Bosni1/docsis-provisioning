create table {:SCHEMA:}device (
  name varchar(128) null,
  parentid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  ownerid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  devicelevel varchar(4) not null,
  devicerole varchar(64)[] null,
  modelid int8 null,
  serialnumber varchar(128) null
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'device' );

