create table {:SCHEMA:}class_of_service (
  classid varchar(24) not null unique,
  name varchar(256) not null,
  official_name varchar(128) null,
  info text null  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'class_of_service' );

create table {:SCHEMA:}type_of_service (
  typeid varchar(24) not null unique,
  name varchar(128) not null,
  official_name varchar(128) null,
  info text null,
  classmap int8[] not null  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'type_of_service' );