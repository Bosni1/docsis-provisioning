-- $Id:$
create table {:SCHEMA:}city (
  name varchar(64) not null unique,
  handle varchar(16) null,
  default_postal_code varchar(16) null
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'city' );

create table {:SCHEMA:}street (
  name varchar(64) not null,
  handle varchar(16) not null,
  "prefix" varchar(5) null default 'ul',
  cityid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  default_postal_code varchar(16) null,
  UNIQUE (name, cityid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'street' );

create table {:SCHEMA:}street_aggregate (
  name varchar(64) not null unique,
  streetid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'street_aggregate' );

create table {:SCHEMA:}building (
  number varchar(16) not null,
  handle varchar null,
  streetid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  postal_code varchar(16) null
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'building' );

create table {:SCHEMA:}location (  
  number varchar(16) null,
  handle varchar(24) null,
  buildingid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  entrance varchar(3) null,
  floor varchar(3) null,
  unique (number, buildingid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'location' );

CREATE FUNCTION {:SCHEMA:}location_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || s.name || ' ' || b.number || coalesce('/' || l.number, '') as repr INTO r 
    FROM {:SCHEMA:}location l, {:SCHEMA:}building b, {:SCHEMA:}street s, {:SCHEMA:}city c WHERE 
       l.buildingid = b.objectid AND b.streetid = s.objectid AND s.cityid = c.objectid
       AND l.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;
