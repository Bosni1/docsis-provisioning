-- $Id$
create table {:SCHEMA:}subscriber (
  subscriberid integer not null unique,
  name varchar(256) not null,    
  primarylocationid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  postaladdress varchar(512) null,  
  info text null,
  email varchar(128)[] null,
  telephone varchar(32)[] null
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'subscriber' );


create table {:SCHEMA:}service (
  subscriberid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  typeofservice int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  classofservice int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  parentservice int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  locationid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NOT NULL,
  handle varchar(24) NULL,
  status smallint not null default 1  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'service' );

