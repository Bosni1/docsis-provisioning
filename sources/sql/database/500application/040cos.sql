create table {:SCHEMA:}class_of_service (
  classid varchar(8) not null unique,
  name varchar(128) not null,
  classparams varchar(256)[] not null  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'class_of_service' );

create table {:SCHEMA:}type_of_service (
  typeid varchar(8) not null unique,
  name varchar(128) not null,
  classmap int8[] not null  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'type_of_service' );