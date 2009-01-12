-- $Id:$
CREATE TABLE {:SCHEMA:}city (
  name varchar(64) not null unique,
  handle varchar(16) null,
  default_postal_code varchar(16) null
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'city' );

CREATE TABLE {:SCHEMA:}street (
  name varchar(64) not null,
  handle varchar(16) not null,
  "prefix" varchar(5) null default 'ul',
  cityid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  default_postal_code varchar(16) null,
  UNIQUE (name, cityid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'street' );

CREATE TABLE {:SCHEMA:}street_aggregate (
  name varchar(64) not null unique,
  streetid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'street_aggregate' );

CREATE TABLE {:SCHEMA:}building (
  number varchar(16) not null,
  handle varchar null,
  streetid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  postal_code varchar(16) null
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'building' );

CREATE TABLE {:SCHEMA:}location (  
  number varchar(16) null,
  handle varchar(24) null,
  buildingid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  entrance varchar(3) null,
  floor varchar(3) null,
  unique (number, buildingid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'location' );

CREATE FUNCTION {:SCHEMA:}street_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || coalesce(s.prefix || '.', '') || s.name as repr INTO r 
    FROM {:SCHEMA:}city c, {:SCHEMA:}street s WHERE 
       s.cityid = c.objectid AND s.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION {:SCHEMA:}building_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || coalesce(s.prefix || '.', '') || s.name  || ' ' || b.number as repr INTO r 
    FROM {:SCHEMA:}building b, {:SCHEMA:}street s, {:SCHEMA:}city c WHERE 
       b.streetid = s.objectid AND s.cityid = c.objectid
       AND b.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION {:SCHEMA:}location_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || coalesce(s.prefix || '.', '') || s.name || ' ' || b.number || coalesce('/' || l.number, '') as repr INTO r 
    FROM {:SCHEMA:}location l, {:SCHEMA:}building b, {:SCHEMA:}street s, {:SCHEMA:}city c WHERE 
       l.buildingid = b.objectid AND b.streetid = s.objectid AND s.cityid = c.objectid
       AND l.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION {:SCHEMA:}location_generic_handle (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT coalesce(c.handle || '/', '') || coalesce(s.handle , '') || coalesce(b.number, '') 
    || coalesce('/' || l.number, '') as repr INTO r 
    FROM {:SCHEMA:}location l, {:SCHEMA:}building b, {:SCHEMA:}street s, {:SCHEMA:}city c WHERE 
       l.buildingid = b.objectid AND b.streetid = s.objectid AND s.cityid = c.objectid
       AND l.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;


