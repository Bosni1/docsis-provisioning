----------------------------------------------------------------------------------------------------
--
-- database/000system.sql
----------------------------------------------------------------------------------------------------
-- $Id:$
drop schema if exists pv cascade;
create schema pv;
create language plpgsql;

SET default_with_oids=TRUE;
----------------------------------------------------------------------------------------------------
--
-- database/001base.sql
----------------------------------------------------------------------------------------------------
-- $Id:$

--
-- This is the table to which all references are actually made.
--
create table pv.objectids (
  objectid int8 primary key
);
-- create index idx_objectids_objectid on pv.objectids (objectid);

--
-- Objects' textual representations are kept here
--
create table pv.object_search_txt (
  objectid int8 PRIMARY KEY,
  txt varchar(256),
  txt_vector tsvector
);
-- create index object_search_txt on pv.object_search_txt USING gin( txt_vector );

--
-- Expressions used to generate objects' text representations.
--
create table pv.object_txt_expressions (
  objecttype name NOT NULL PRIMARY KEY,
  objecttxtexpr text NOT NULL
);
create index idx_object_txt_expr_objecttype on pv.object_txt_expressions (objecttype);

--
-- Change object_search_txt when txt_expression changes.
--
create function pv.object_txt_expression_change() RETURNS trigger AS $body$  
  BEGIN
    IF (NEW.objecttxtexpr <> OLD.objecttxtexpr) THEN    
      UPDATE pv.object_search_txt AS ost SET 
        txt = pv.obj_txt_repr ( ost.objectid::int8, o.objecttype::name )
        --, txt_vector = to_tsvector(pv.obj_txt_repr ( ost.objectid::int8, o.objecttype::name ))
        FROM pv.object o WHERE o.objectid = ost.objectid AND o.objecttype = NEW.objecttype;
    END IF;    
    RETURN NEW;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER bulk_update_txt_expressions AFTER UPDATE ON pv.object_txt_expressions
FOR EACH ROW EXECUTE PROCEDURE pv.object_txt_expression_change();


--
-- Base table.
--
create table pv.object (
  objectid SERIAL8,
  objectscope smallint NOT NULL DEFAULT 0,
  objectcreation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  objectmodification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  
  objecttype name NOT NULL DEFAULT 'object',
  PRIMARY KEY (objectid)
);
CREATE VIEW pv.objecttxt AS SELECT o.*, t.txt as objecttxt 
    FROM pv.object o LEFT JOIN pv.object_search_txt t ON o.objectid = t.objectid;

-- HANDLER CALLED BEFORE ACTION ON OBJECT ROWS
-- on insert: insert objectis into "objectids", set objecttype
-- on update: set object modification time
-- on delete: delete from "objectids"
create function pv.handle_object_lifespan_before() RETURNS trigger AS $handle_object_lifespan$
  BEGIN
    IF (TG_OP = 'INSERT') THEN
      INSERT INTO pv.objectids VALUES (NEW.objectid);
      NEW.objecttype := TG_TABLE_NAME;
      RETURN NEW;      
    END IF;
    
    IF (TG_OP = 'UPDATE') THEN
      NEW.objectmodification := CURRENT_TIMESTAMP;
      RETURN NEW;
    END IF;    
    
    IF (TG_OP = 'DELETE') THEN
      DELETE FROM pv.objectids WHERE objectid = OLD.objectid;
      RETURN OLD;
    END IF;
    
  END;
$handle_object_lifespan$ LANGUAGE plpgsql;



-- HANDLER CALLED AFTER ACTION ON OBJECT ROWS
-- on insert: set object_search_txt
-- on update: update object_search_txt
create function pv.handle_object_lifespan_after() RETURNS trigger AS $handle_object_lifespan$
  DECLARE
    txt_expr text;
  BEGIN
    IF (TG_OP = 'INSERT') THEN      
      INSERT INTO pv.object_search_txt (objectid, txt) VALUES ( NEW.objectid, pv.obj_txt_repr (NEW.objectid, NEW.objecttype) );
    END IF;
    IF (TG_OP = 'UPDATE') THEN
      txt_expr := pv.obj_txt_repr (NEW.objectid, NEW.objecttype);
      
      UPDATE pv.object_search_txt SET txt = txt_expr WHERE objectid = NEW.objectid;
    END IF;    
    RETURN NEW;      
  END;
$handle_object_lifespan$ LANGUAGE plpgsql;

--
-- This function sets up a table as a subtable of "object"
-- This involves:
--  1. creating triggers handling object lifespan
--  2. setting primary keys to "objectid"
--  3. setting a default object_txt_expression
--
create function pv.setup_object_subtable (classname text) returns text as $setup$
  DECLARE
    triggername text;    
  BEGIN
    triggername := 'object_' || classname || '_creation_';
    EXECUTE 'CREATE TRIGGER ' || quote_ident(triggername || '_bf') 
        || ' BEFORE INSERT OR UPDATE OR DELETE ON pv.' || classname || ' FOR EACH ROW EXECUTE PROCEDURE '
        || ' pv.handle_object_lifespan_before();';
    EXECUTE 'CREATE TRIGGER ' || quote_ident(triggername || '_af') 
        || ' AFTER INSERT OR UPDATE OR DELETE ON pv.' || classname || ' FOR EACH ROW EXECUTE PROCEDURE '
        || ' pv.handle_object_lifespan_after();';
    EXECUTE 'ALTER TABLE pv.' || classname || ' ADD PRIMARY KEY (objectid)';
    EXECUTE 'INSERT INTO pv.object_txt_expressions (objecttype, objecttxtexpr) VALUES ( ''' || classname || ''', ''objecttype || objectid'' )';
--    EXECUTE 'ALTER TABLE pv.' || classname || ' ADD UNIQUE (objectid)';
    RETURN classname || ' triggers are set.';
  END;
$setup$ LANGUAGE plpgsql;

--
--  return text representation for an object
--
CREATE FUNCTION pv.obj_txt_repr (objid int8, objtype name) returns text as $repr$
  DECLARE
    expr text;
    repr text;
  BEGIN
    SELECT e.objecttxtexpr INTO expr FROM pv.object_txt_expressions e INNER JOIN pv.object o ON o.objecttype = e.objecttype AND o.objectid = objid LIMIT 1;  
    IF NOT FOUND THEN 
      RETURN '<null>';
    END IF;
    EXECUTE 'SELECT ' || expr || ' FROM pv.' || objtype || ' WHERE objectid = ' || objid INTO repr;
    RETURN repr;
  END;
$repr$ LANGUAGE plpgsql;

create function pv.update_search_txt(objtype name) RETURNS BOoLEAn AS $body$  
  BEGIN
      UPDATE pv.object_search_txt AS ost SET 
        txt = pv.obj_txt_repr ( ost.objectid::int8, o.objecttype::name ) 
        FROM pv.object o WHERE o.objectid = ost.objectid AND o.objecttype = objtype;    
      return TRUE;  
  END;
$body$ LANGUAGE plpgsql;

create function pv.get_search_txt(objid int8) RETURNS varchar AS $body$  
  declare
  r varchar;
  BEGIN
      SELECT txt INTO r FROM pv.object_search_txt  WHERE objectid = objid;
      return r;  
  END;
$body$ LANGUAGE plpgsql;

----------------------------------------------------------------------------------------------------
--
-- database/002meta.sql
----------------------------------------------------------------------------------------------------
-- $Id:$

--
-- Table information used by GUI
--
CREATE TABLE pv.table_info (
  schema name not null,
  name name not null unique,  
  superclass int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  subclasses int8[] null,
  label varchar(128) null,
  title varchar(128) null,
  info text null,
  pprint_expression text default '#%(objectid)s',
  pk name not null default 'objectid',
  disabledfields name[] not null default '{}',
  excludedfields name[] not null default '{}',  
  txtexpression text null,  
  recordlisttoolbox varchar(128)[] not null default '{}',
  recordlistpopup varchar(128)[] not null default '{}',
  knownflags varchar(64)[] not null default '{}',
  knownparams varchar(64)[] not null default '{}',
  hasevents boolean not null default false,
  hasnotes boolean not null default false,
  UNIQUE (schema, name)
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'table_info' );


--
-- Table column information used by GUI
--
CREATE TABLE pv.field_info (  
  lp smallint not null,
  name name not null,
  path varchar(128) null,
  type name not null,
  ndims smallint not null,
  length smallint null,
  classid int REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  reference int REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  arrayof int REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  choices varchar(256)[] NOT NULL DEFAULT '{}',
  constraintid oid NULL,
  reference_editable bit not null default '0',
  pprint_fkexpression text default null,  
  required bit not null default '0',
  protected bit not null default '0',
  nullable bit not null default '1',
  label varchar(128) null,
  quickhelp varchar(256) null,
  helptopic varchar(128) null,
  info text null,
  editor_class name default null,
  editor_class_params varchar(128)[] null default '{}'
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'field_info' );

--
-- Table column information used by GUI
--
CREATE TABLE pv.mtm_relationship (  
  mtm_table_name name not null,
  relationship_name name not null,
  table_1 name not null,
  table_1_handle name not null,
  table_1_column name not null,
  table_2 name not null,
  table_2_handle name not null,
  table_2_column name not null,
  unique (table_1, table_1_handle),
  unique (table_2, table_2_handle),
  unique (relationship_name)
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'mtm_relationship' );

CREATE VIEW pv.map_class_ids AS
select c.oid as systemid, ac.objectid as localid 
from pv.table_info ac inner join pg_class c on c.relname = ac.name 
inner join pg_namespace n on n.oid = c.relnamespace 
where n.nspname = ac.schema;

CREATE VIEW pv.reference_info AS
select 'PERFORM pv.set_reference ( ''' || c1.name || '.' || f1.name || ''', ''' || c2.name || ''');'  from 
    pv.table_info c1 INNER JOIN pv.field_info f1 ON f1.classid = c1.objectid 
    INNER JOIN pv.table_info c2 ON c2.objectid = f1.reference 
    WHERE f1.reference is not null;

CREATE VIEW pv.all_references AS
select c1.objectid as reftableid, c1.name as reftable,  f1.name as refcolumn, f1.constraintid as refcon from 
    pv.table_info c1 INNER JOIN pv.field_info f1 ON f1.classid = c1.objectid 
    INNER JOIN pv.table_info c2 ON c2.objectid = f1.reference 
    WHERE f1.reference is not null;

-- create table pv.x ( x text );
create function pv.handle_field_info_change() RETURNS trigger AS $body$
  DECLARE
    tname text;
    mytable RECORD;
    subf RECORD;
  BEGIN
    IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE') THEN
      SELECT name INTO tname FROM pv.table_info WHERE objectid = NEW.classid;      
      NEW.path = tname || '.' || NEW.name;            
      IF (TG_OP = 'UPDATE') THEN
        SELECT * INTO mytable FROM pv.table_info WHERE objectid = NEW.classid;
        IF (NEW.reference <> OLD.reference) THEN          
--          INSERT INTO pv.x VALUES ( mytable.name || ' ' || NEW.name );
--          FOR subf IN SELECT f.* FROM pv.field_info f, pv.table_info t 
--            WHERE t.objectid = ANY ( mytable.subclasses) AND f.classid = t.objectid AND
--            f.
          UPDATE pv.field_info f SET reference = NEW.reference 
            FROM pv.table_info t WHERE t.objectid = ANY ( mytable.subclasses ) AND
            f.name = NEW.name AND f.classid = t.objectid;
        END IF;
      END IF;
      RETURN NEW;      
    END IF;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER set_field_info_path BEFORE UPDATE OR INSERT ON pv.field_info 
FOR EACH ROW EXECUTE PROCEDURE pv.handle_field_info_change();

CREATE FUNCTION pv.table_object_id ( tblname name ) returns int8 as $$
DECLARE
  id int8;
BEGIN
  SELECT objectid INTO id FROM pv.table_info WHERE name = tblname LIMIT 1;
  RETURN id;
END;
$$ LANGUAGE plpgsql;

--
-- Set the subclasses array in each table_info record, starting at "tableobjectid" and proceeding
-- recursively through the inheritance tree.
--
CREATE FUNCTION pv.fill_subclass_array ( tableobjectid int8 ) returns int as $$
DECLARE
  tbl RECORD;
  tbl2 RECORD;
BEGIN
  UPDATE pv.table_info SET subclasses = '{}' WHERE objectid = tableobjectid;
  FOR tbl IN SELECT * FROM pv.table_info WHERE superclass = tableobjectid LOOP
    PERFORM pv.fill_subclass_array ( tbl.objectid );
    SELECT * INTO tbl2 FROM pv.table_info WHERE objectid = tbl.objectid;
    UPDATE pv.table_info SET subclasses = array_cat (subclasses, array_append(tbl2.subclasses, tbl2.objectid)) WHERE objectid = tableobjectid;
  END LOOP;
  RETURN 1;
END;
$$ LANGUAGE plpgsql;


create function pv.handle_table_info_change() RETURNS trigger AS $body$
  DECLARE
    tname text;
  BEGIN
    IF (NEW.txtexpression <> OLD.txtexpression) THEN
      UPDATE pv.object_txt_expressions SET objecttxtexpr = NEW.txtexpression WHERE objecttype = NEW.name;      
    END IF;    
    RETURN NEW;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER set_table_info BEFORE UPDATE ON pv.table_info 
FOR EACH ROW EXECUTE PROCEDURE pv.handle_table_info_change();

--
--  Since references are not automatically inherited, we do it manually.
--
CREATE FUNCTION pv.propagate_references () returns int as $$
DECLARE
  refs RECORD;
  child RECORD;
  stbl RECORD;
  con RECORD;
  cmd text;
BEGIN
  FOR refs IN SELECT * FROM pv.all_references LOOP
    SELECT * INTO stbl FROM ONLY pv.table_info WHERE objectid = refs.reftableid;
    FOR child IN SELECT * FROM pv.table_info WHERE objectid = ANY ( stbl.subclasses ) LOOP
      cmd := 'ALTER TABLE pv.' || child.name || ' ADD  FOREIGN KEY (' || refs.refcolumn || ') REFERENCES pv.objectids ';
      SELECT * INTO con FROM pg_constraint WHERE oid = refs.refcon;                       
      
      cmd := cmd || pv.constraint_construct ( 'DELETE', con.confdeltype );
      cmd := cmd || ' ' || pv.constraint_construct ( 'UPDATE', con.confupdtype );
      EXECUTE cmd;               
      -- insert into pv.x values (cmd);      
      cmd := 'UPDATE pv.field_info SET reference = pv.table_object_id (''object'') WHERE path = ''' || child.name || '.' || refs.refcolumn || '''';
      EXECUTE cmd;      
    END LOOP;
  END LOOP;
  RETURN 0;
END;
$$ language plpgsql;

--
-- Use this to point to the actual referenced tables.
-- In "CREATE TABLE" we create references to the objectids table.
--
CREATE FUNCTION pv.set_reference ( field text, tbl text) returns int as $$
DECLARE
  idx_tbl varchar;
  idx_col varchar;
BEGIN
  idx_tbl := substr(field, 0, strpos(field, '.')) ; 
  idx_col := substr(field, strpos(field, '.')+1);
  UPDATE pv.field_info SET reference = pv.table_object_id ( tbl ) WHERE path = field;
  EXECUTE 'CREATE INDEX idx_ref_' || tbl  || '_' || replace(field,'.','_') || ' ON pv.' || idx_tbl
  || ' ( ' || idx_col || ' ) '; 
  RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pv.set_editor_class ( field text, editor text, params varchar[]) returns int as $$
BEGIN
  UPDATE pv.field_info SET editor_class = editor, editor_class_params = params  
  WHERE path = field;
  RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pv.constraint_construct ( ev text, t text) returns text as $$
DECLARE
  r text;
BEGIN
  IF (t = 'c') THEN 
    r = 'CASCADE';
  ELSEIF (t = 'n') THEN 
    r = 'SET NULL';
  ELSEIF (t = 'a') THEN 
    r = 'NO ACTION';
  ELSEIF (t = 'd') THEN 
    r = 'SET DEFAULT';
  ELSEIF (t = 'r') THEN 
    r = 'RESTRICT';
  ELSE 
    RETURN '';  
  END IF;
  return 'ON ' || ev || ' ' || r;  
END;
$$ LANGUAGE plpgsql;


CREATE FUNCTION pv.create_mtm_relationship ( t1 name, t2 name, rname name) returns text as $$
DECLARE
  tname name;
BEGIN
  tname = '_mtm_' || rname;
  EXECUTE 'CREATE TABLE pv.' || tname || ' ( ' ||
  t1 || 'id int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, ' ||
  t2 || 'id int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, ' ||
  ' refdata int8 NULL, ' ||
  ' PRIMARY KEY (' || t1 || 'id, ' || t2 || 'id) ' ||
  ' ) ';
  INSERT INTO pv.mtm_relationship (mtm_table_name, relationship_name, 
    table_1, table_1_handle, table_1_column, 
    table_2, table_2_handle, table_2_column)
    VALUES (tname, rname, t1, 'related_' || t2, t1 || 'id',
            t2, 'related_' || t1, t2 || 'id' );
  return tname;  
END;
$$ LANGUAGE plpgsql;

SELECT pv.create_mtm_relationship ( 'device', 'service', 'service_device' );


----------------------------------------------------------------------------------------------------
--
-- database/500application/010objectaddin.sql
----------------------------------------------------------------------------------------------------
-- $Id:$

create table pv.event (
  refobjectid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  executedtime timestamp not null default current_timestamp,
  class smallint not null default 0,
  severity smallint not null default 0,
  planned bit not null default '0',
  initiator varchar(32) not null default 'internal',
  data text,
  check (refobjectid <> objectid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'event' );

create table pv.note (
  refobjectid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  timeadded timestamp not null default current_timestamp,
  addedby varchar(64) null,
  content text,
  check (refobjectid <> objectid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'note' );

create table pv.object_parameter (
  refobjectid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  parametername varchar(64) not null,
  content text not null,
  check (refobjectid <> objectid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'object_parameter' );

create table pv.object_flag (
  refobjectid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  flagname varchar(64) not null,
  unique (refobjectid, flagname),
  check (refobjectid <> objectid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'object_flag' );

create function pv.object_has_flag (objid int8, fname varchar) returns boolean AS $obj$
  BEGIN
    SELECT * FROM pv.object_flag WHERE refobjectid = objid AND upper(flagname) = upper(fname);
    IF NOT FOUND THEN
      RETURN FALSE;
    ELSE
      RETURN TRUE;
    END IF;
  END;
$obj$ LANGUAGE plpgsql;

create function pv.object_param (objid int8, pname varchar) returns varchar AS $obj$
  DECLARE
    cnt varchar;
  BEGIN
    SELECT content INTO cnt FROM pv.object_parameter WHERE refobjectid = objid 
    AND upper(parametername) = upper(pname);
    IF NOT FOUND THEN
      RETURN NULL;
    ELSE
      RETURN cnt;
    END IF;
  END;
$obj$ LANGUAGE plpgsql;

----------------------------------------------------------------------------------------------------
--
-- database/500application/020ipaddressing.sql
----------------------------------------------------------------------------------------------------
-- $Id:$

create table pv.ip_subnet (
  subnetgroupid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  name varchar(64) not null,
  scope varchar(64) null,  
  designation smallint[] not null default '{1}',
  network cidr not null unique,
  gateway inet null,
  active bit not null default '1',
  allownew bit not null default '1',
  dhcpserver inet null  
) inherits (pv."object");
SELECT pv.setup_object_subtable ('ip_subnet' );

create function pv.update_ip_reservations_subnet() returns TRIGGER AS $trig$
DECLARE
   subnet_network cidr;
BEGIN  
  IF (TG_OP = 'UPDATE') OR (TG_OP = 'INSERT') THEN
    subnet_network = NEW.network;
  END IF;
  IF (TG_OP = 'DELETE') THEN
    subnet_network = OLD.network;  
  END IF;
  
  UPDATE pv.ip_reservation ip SET 
  subnetid = (SELECT objectid FROM pv.ip_subnet WHERE network >> ip.address ORDER BY masklen(network) DESC LIMIT 1 )
  WHERE ip.address << subnet_network;
  IF (TG_OP = 'UPDATE') OR (TG_OP = 'INSERT') THEN
    RETURN NEW;
  END IF;
  IF (TG_OP = 'DELETE') THEN
    RETURN OLD;
  END IF;
END;
$trig$ language plpgsql;
CREATE TRIGGER ip_subnet_on_update_reservations AFTER INSERT OR UPDATE OR DELETE ON pv.ip_subnet
  FOR EACH ROW EXECUTE PROCEDURE pv.update_ip_reservations_subnet();

create table pv.ip_subnet_group (
  name varchar(64) not null,
  info text null
) inherits (pv."object");
SELECT pv.setup_object_subtable ('ip_subnet_group' );

create table pv.ip_reservation (
  ownerid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  subnetid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  interfaceid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  address inet not null unique,
  designation smallint not null default 1,
  scope smallint not null default 1,
  dhcp bit not null default '1',
  lastused timestamp null,
  state smallint not null default 1  
) inherits (pv."object");
SELECT pv.setup_object_subtable ('ip_reservation' );

create function pv.check_ip_reservation_uniqueness() returns TRIGGER AS $ip_uniq$
  DECLARE
    addrcnt int;
    subnetid int8;
    cnt int;
  BEGIN
    SELECT count(address) FROM pv.ip_reservation WHERE address >>= NEW.address AND objectid <> NEW.objectid AND designation = NEW.designation into addrcnt;
    IF (addrcnt > 0) THEN
      RAISE EXCEPTION 'Duplicate IP address reservation requested. (designation: ' || NEW.designation || ')';
    END IF;    
    SELECT "objectid" FROM pv.ip_subnet WHERE network >> NEW.address ORDER BY masklen(network) DESC LIMIT 1 INTO subnetid;
    GET DIAGNOSTICS cnt = ROW_COUNT;
    IF (cnt > 0) THEN 
      NEW.subnetid = subnetid;
    ELSE
      NEW.subnetid = NULL;
    END IF;
    RETURN NEW;
  END;
$ip_uniq$ language plpgsql;
CREATE TRIGGER ip_reservation_uniqueness_check BEFORE INSERT OR UPDATE ON pv.ip_reservation 
  FOR EACH ROW EXECUTE PROCEDURE pv.check_ip_reservation_uniqueness();


----------------------------------------------------------------------------------------------------
--
-- database/500application/030location.sql
----------------------------------------------------------------------------------------------------
-- $Id:$
CREATE TABLE pv.city (
  name varchar(64) not null unique,
  handle varchar(16) null,
  default_postal_code varchar(16) null
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'city' );

CREATE TABLE pv.street (
  name varchar(64) not null,
  handle varchar(16) not null,
  "prefix" varchar(5) null default 'ul',
  cityid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  default_postal_code varchar(16) null,
  UNIQUE (name, cityid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'street' );

CREATE TABLE pv.street_aggregate (
  name varchar(64) not null unique,
  streetid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'street_aggregate' );

CREATE TABLE pv.building (
  number varchar(16) not null,
  handle varchar null,
  streetid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  postal_code varchar(16) null
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'building' );

CREATE TABLE pv.location (  
  number varchar(16) null,
  handle varchar(24) null,
  buildingid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  entrance varchar(3) null,
  floor varchar(3) null,
  unique (number, buildingid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'location' );

CREATE FUNCTION pv.street_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || coalesce(s.prefix || '.', '') || s.name as repr INTO r 
    FROM pv.city c, pv.street s WHERE 
       s.cityid = c.objectid AND s.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pv.building_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || coalesce(s.prefix || '.', '') || s.name  || ' ' || b.number as repr INTO r 
    FROM pv.building b, pv.street s, pv.city c WHERE 
       b.streetid = s.objectid AND s.cityid = c.objectid
       AND b.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pv.location_txt_expression (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT c.name || ' ' || coalesce(s.prefix || '.', '') || s.name || ' ' || b.number || coalesce('/' || l.number, '') as repr INTO r 
    FROM pv.location l, pv.building b, pv.street s, pv.city c WHERE 
       l.buildingid = b.objectid AND b.streetid = s.objectid AND s.cityid = c.objectid
       AND l.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pv.location_generic_handle (objid int8) returns varchar AS $$
  DECLARE
    r varchar;    
  BEGIN
    SELECT coalesce(c.handle || '/', '') || coalesce(s.handle , '') || coalesce(b.number, '') 
    || coalesce('/' || l.number, '') as repr INTO r 
    FROM pv.location l, pv.building b, pv.street s, pv.city c WHERE 
       l.buildingid = b.objectid AND b.streetid = s.objectid AND s.cityid = c.objectid
       AND l.objectid = objid
       LIMIT 1;    
    RETURN r;
  END;
$$ LANGUAGE plpgsql;


----------------------------------------------------------------------------------------------------
--
-- database/500application/040cos.sql
----------------------------------------------------------------------------------------------------
create table pv.class_of_service (
  classid varchar(24) not null unique,
  name varchar(256) not null,
  official_name varchar(256) null,
  info text null  
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'class_of_service' );

create table pv.type_of_service (
  typeid varchar(24) not null unique,
  name varchar(128) not null,
  official_name varchar(256) null,
  info text null,
  classmap int8[] not null  
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'type_of_service' );----------------------------------------------------------------------------------------------------
--
-- database/500application/050subscriber.sql
----------------------------------------------------------------------------------------------------
-- $Id$
create table pv.subscriber (
  subscriberid integer not null unique,
  name varchar(256) not null,    
  primarylocationid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  postaladdress varchar(512) null,  
  info text null,
  email varchar(128)[] null,
  telephone varchar(32)[] null
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'subscriber' );


create table pv.service (
  subscriberid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  typeofservice int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  classofservice int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  parentservice int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  locationid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NOT NULL,
  handle varchar(24) NULL,
  status smallint not null default 1  
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'service' );

----------------------------------------------------------------------------------------------------
--
-- database/500application/060device.sql
----------------------------------------------------------------------------------------------------
create table pv.device (
  name varchar(128) null,
  parentid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  ownerid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  devicelevel varchar(4) not null,
  devicerole varchar(64)[] null,
  modelid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  serialnumber varchar(128) null
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'device' );

create table pv.device_model (
  name varchar(128) null,
  defaultroles varchar(64)[] null,
  info text
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'device_model' );


CREATE FUNCTION pv.get_device_text (objid int8) returns text AS $$
  DECLARE
    dev RECORD;
    txt text;
    cnt integer;
  BEGIN
    SELECT d.*, m.name as modelname INTO dev FROM pv.device d LEFT JOIN pv.device_model m ON m.objectid = d.modelid WHERE d.objectid = objid LIMIT 1;
    GET DIAGNOSTICS cnt = ROW_COUNT;

    IF cnt = 0 THEN
       RETURN NULL;
    END IF;

    IF 'docsis_cable_modem' = ANY ( dev.devicerole ) THEN 
       txt := 'MODEM KABLOWY';
       IF 'nat_router' = ANY ( dev.devicerole ) THEN
          txt := txt || ' z ROUTEREM';
       END IF;
       IF 'wireless_ap' = ANY ( dev.devicerole ) THEN
          txt := txt || ' z WiFi';
       END IF;
       IF 'sip_client' = ANY ( dev.devicerole ) THEN
          txt := txt || ' + Bramka VoIP';
       END IF;
    ELSIF 'cpe' = ANY ( dev.devicerole ) THEN
       IF 'wireless_client' = ANY ( dev.devicerole ) THEN
          txt := 'KARTA BEZPRZEWODOWA';
       ELSE
          txt := 'KARTA SIECIOWA';
       END IF;
    ELSIF 'sip_client' = ANY ( dev.devicerole ) THEN
       txt := 'Bramka VoIP';
    ELSIF 'nat_router' = ANY ( dev.devicerole ) THEN
       IF 'wireless_ap' = ANY ( dev.devicerole ) THEN
           txt := 'ROUTER z WiFi';
       ELSE 
           txt := 'ROUTER';
       END IF;
    ELSE    
       txt := dev.name || ' ' || dev.devicerole::text;
    END IF;
    txt := txt || ' ' || coalesce(dev.modelname,'');
    RETURN txt;
  END;
$$ LANGUAGE plpgsql;
----------------------------------------------------------------------------------------------------
--
-- database/500application/070role.sql
----------------------------------------------------------------------------------------------------
-- $Id:$
create table pv.device_role (
  deviceid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'device_role');

create table pv.cpe (
  macid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  name varchar(32) null,
  info text null,
  os varchar(32) null,
  UNIQUE (macid)
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'cpe');

create table pv.docsis_cable_modem (
  cmtsid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  downstreamid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  upstreamid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  hfcmacid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NOT NULL,
  usbmacid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  lanmacid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  mgmtmacid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  customersn varchar(128) NULL,
  maxcpe smallint NOT NULL DEFAULT 1,  
  cpemacfilter bit NOT NULL DEFAULT '0',
  cpeipfilter bit NOT NULL DEFAULT '1',
  netbiosfilter bit NOT NULL DEFAULT '1',
  docsisversion numeric(3,2) NOT NULL DEFAULT 1.00,
  nightsurf bit NULL,
  networkaccess bit NOT NULL DEFAULT '1',
  upgradefilename varchar(128) NULL,
  upgradeserver inet NULL,
  configfilename varchar(128) NULL,    
  cvc int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  vendoroptions bytea NULL,
  VENDOR varchar(128) NULL ,
  HW_REV varchar(128) NULL,
  SW_REV varchar(128) NULL,
  MODEL varchar(128) NULL,
  BOOTR varchar(128) NULL,
  BASECAP varchar(128) NULL
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ('docsis_cable_modem' );

create table pv.routeros_device (
  swmajor smallint null,
  swminor smallint null,
  mgmt_user varchar(16) null,
  mgmt_pass varchar(16) null,
  configuration text null
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ('routeros_device' );

create table pv.core_switch (
  ports smallint not null default 8
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ('core_switch' );

create table pv.core_switch_port (
  switchid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  portid int not null,
  portname varchar(16) null,
  linkedto int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  UNIQUE (switchid, portid)
) inherits (pv."object");
SELECT pv.setup_object_subtable ('core_switch_port' );

create table pv.core_router (
  dhcp_relay bit not null default '0',
  default_nexthop inet null
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'core_router' );

create table pv.core_router_bridged_network (
  routerid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  subnetid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NULL
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'core_router_bridged_network' );

create table pv.nat_router (
  localaddr inet not null,
  dhcp bit not null default '1',
  lanports smallint null,
  wanmacid int8 REFERENCES pv.objectids ON DELETE CASCADE ON UPDATE CASCADE NULL
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'nat_router' );

create table pv.wireless (
  interfaceid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  band varchar(32) null,
  frequency smallint null,
  channelwidth smallint null,
  UNIQUE (interfaceid)
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'wireless' );

create table pv.wireless_client (
  accesspointid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  networkaccess bit not null default '1'
) inherits (pv."wireless");
SELECT pv.setup_object_subtable ( 'wireless_client' );
-- on update (insert): if network access changed and accesspoint set - update acl of accesspoint
-- on delete: remove from acl of accesspoint

create table pv.wireless_ap (
  essid varchar(128) null,
  acl macaddr[] null
) inherits (pv."wireless");
SELECT pv.setup_object_subtable ( 'wireless_ap' );

create table pv.wireless_link (
  otherend int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  mode smallint not null default 1
) inherits (pv."wireless");
SELECT pv.setup_object_subtable ( 'wireless_link' );

create table pv.sip_client (
  server varchar(256) not null,
  account varchar(256) not null,
  pass varchar(256) not null,
  pstn_number varchar(64) not null
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'sip_client' );

create function pv.handle_all_device_role_change() RETURNS trigger AS $body$
  DECLARE
    deviceid int8;
    mytable RECORD;
    subf RECORD;
  BEGIN
  IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE') THEN
    deviceid := NEW.deviceid;
  ELSIF (TG_OP = 'DELETE') THEN
    deviceid := OLD.deviceid;
  END IF;  
  UPDATE pv.object_search_txt SET txt = pv.obj_txt_repr ( deviceid, 'device' ) WHERE
      objectid = deviceid;
  IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE') THEN
    RETURN NEW;
  ELSIF (TG_OP = 'DELETE') THEN
    RETURN OLD;
  END IF;
  END;
$body$ LANGUAGE plpgsql;

create function pv.set_all_device_role_triggers() RETURNS void AS $body$
DECLARE
   device_role RECORD;
   trigger_cmd text;
BEGIN
   FOR device_role IN select tc.* from pv.table_info tc, pv.table_info tp where tc.objectid = ANY( tp.subclasses ) AND tp.name = 'device_role' LOOP
      trigger_cmd := 'CREATE TRIGGER update_parent_device_name_' || device_role.name || 
        ' AFTER UPDATE OR INSERT OR DELETE ON pv.' || device_role.name || 
        ' FOR EACH ROW EXECUTE PROCEDURE pv.handle_all_device_role_change();';      
      EXECUTE trigger_cmd;
   END LOOP;
END;
$body$ LANGUAGE plpgsql;


-- CREATE TRIGGER set_field_info_path AFTER UPDATE OR INSERT OR DELETE ON pv.
-- FOR EACH ROW EXECUTE PROCEDURE pv.handle_field_info_change();

----------------------------------------------------------------------------------------------------
--
-- database/500application/080interface.sql
----------------------------------------------------------------------------------------------------
-- $Id:$
create table pv.mac_interface (  
  mac macaddr null,  
  designation smallint default 1,
  ipreservationid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  deviceid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  ownerid int8 REFERENCES pv.objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  name varchar(32) null,
  type smallint not null default '1',  
  unique (mac, designation)
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'mac_interface' );
CREATE INDEX idx_mac_interface_mac on pv.mac_interface (mac);

CREATE FUNCTION pv.get_interface_mac (objid int8) returns macaddr AS $$
  DECLARE
    m varchar;    
  BEGIN
    SELECT mac INTO m 
    FROM pv.mac_interface WHERE 
       objectid = objid
       LIMIT 1;    
    RETURN m;
  END;
$$ LANGUAGE plpgsql;

create function pv.get_interface_first_ip(interfaceoid int8) returns inet AS $intip$ 
DECLARE
  ip inet;
BEGIN
  SELECT address INTO ip
  FROM pv.ip_reservation i WHERE i.interfaceid = interfaceoid LIMIT 1;
  RETURN ip;
END;
$intip$ LANGUAGE plpgsql;

create function pv.get_device_first_ip(deviceoid int8) returns inet AS $intip$ 
DECLARE
  ip inet;
BEGIN
  SELECT r.address INTO ip
  FROM pv.ip_reservation r, pv.mac_interface i WHERE r.interfaceid = i.objectid  AND 
    i.deviceid = deviceoid LIMIT 1;
  RETURN ip;
END;
$intip$ LANGUAGE plpgsql;

create function pv.get_interface_reserved_ip(interfaceoid int8) returns inet AS $intip$ 
DECLARE
  ip inet;
BEGIN
  SELECT i.address INTO ip
  FROM pv.ip_reservation i, pv.mac_interface m WHERE m.ipreservationid = i.objectid 
     AND m.objectid = interfaceoid LIMIT 1;
  RETURN ip;
END;
$intip$ LANGUAGE plpgsql;
----------------------------------------------------------------------------------------------------
--
-- database/500application/999appmeta.sql
----------------------------------------------------------------------------------------------------

CREATE FUNCTION pv.set_all_references() returns int as $$
BEGIN
 PERFORM pv.set_reference ( 'table_info.superclass', 'table_info');
 
 PERFORM pv.set_reference ( 'field_info.reference', 'table_info');
 PERFORM pv.set_reference ( 'field_info.classid', 'table_info');
 PERFORM pv.set_reference ( 'field_info.arrayof', 'table_info');

 PERFORM pv.set_reference ( 'event.refobjectid', 'object');

 PERFORM pv.set_reference ( 'note.refobjectid', 'object');

 PERFORM pv.set_reference ( 'object_parameter.refobjectid', 'object');

 PERFORM pv.set_reference ( 'object_flag.refobjectid', 'object');

 PERFORM pv.set_reference ( 'ip_subnet.subnetgroupid', 'ip_subnet_group');

 PERFORM pv.set_reference ( 'ip_reservation.ownerid', 'service');
 PERFORM pv.set_reference ( 'ip_reservation.subnetid', 'ip_subnet');
 PERFORM pv.set_reference ( 'ip_reservation.interfaceid', 'mac_interface');

 PERFORM pv.set_reference ( 'street.cityid', 'city');

 PERFORM pv.set_reference ( 'street_aggregate.streetid', 'street');

 PERFORM pv.set_reference ( 'building.streetid', 'street'); 

 PERFORM pv.set_reference ( 'location.buildingid', 'building');

 PERFORM pv.set_reference ( 'subscriber.primarylocationid', 'location');

 PERFORM pv.set_reference ( 'service.subscriberid', 'subscriber');
 PERFORM pv.set_reference ( 'service.parentservice', 'service');
 PERFORM pv.set_reference ( 'service.typeofservice', 'type_of_service');
 PERFORM pv.set_reference ( 'service.classofservice', 'class_of_service');
 PERFORM pv.set_reference ( 'service.locationid', 'location');
 
 PERFORM pv.set_reference ( 'device.ownerid', 'subscriber'); 
 PERFORM pv.set_reference ( 'device.parentid', 'device');
 PERFORM pv.set_reference ( 'device.modelid', 'device_model');
 
 PERFORM pv.set_reference ( 'device_role.deviceid', 'device');
 
 PERFORM pv.set_reference ( 'cpe.deviceid', 'device');
 PERFORM pv.set_reference ( 'cpe.macid', 'mac_interface');
 
 PERFORM pv.set_reference ( 'docsis_cable_modem.deviceid', 'device');
 PERFORM pv.set_reference ( 'docsis_cable_modem.cmtsid', 'device_role');
 PERFORM pv.set_reference ( 'docsis_cable_modem.downstreamid', 'device_role');
 PERFORM pv.set_reference ( 'docsis_cable_modem.hfcmacid', 'mac_interface');
 PERFORM pv.set_reference ( 'docsis_cable_modem.usbmacid', 'mac_interface');
 PERFORM pv.set_reference ( 'docsis_cable_modem.lanmacid', 'mac_interface');
 PERFORM pv.set_reference ( 'docsis_cable_modem.mgmtmacid', 'mac_interface');
 
 PERFORM pv.set_reference ( 'routeros_device.deviceid', 'device');

 PERFORM pv.set_reference ( 'core_switch.deviceid', 'device');
 
 PERFORM pv.set_reference ( 'core_switch_port.switchid', 'core_switch');
 PERFORM pv.set_reference ( 'core_switch_port.linkedto', 'device');
    
 PERFORM pv.set_reference ( 'core_router.deviceid', 'device');
 
 PERFORM pv.set_reference ( 'core_router_bridged_network.routerid', 'device_role');
 PERFORM pv.set_reference ( 'core_router_bridged_network.subnetid', 'ip_subnet');

 PERFORM pv.set_reference ( 'core_router.deviceid', 'nat_router');

 PERFORM pv.set_reference ( 'wireless.deviceid', 'device');
 PERFORM pv.set_reference ( 'wireless.interfaceid', 'mac_interface');

 PERFORM pv.set_reference ( 'wireless_client.deviceid', 'device');
 PERFORM pv.set_reference ( 'wireless_client.interfaceid', 'mac_interface');
 PERFORM pv.set_reference ( 'wireless_client.accesspointid', 'device_role');

 PERFORM pv.set_reference ( 'wireless_ap.deviceid', 'device');
 PERFORM pv.set_reference ( 'wireless_ap.interfaceid', 'mac_interface');

 PERFORM pv.set_reference ( 'wireless_link.deviceid', 'device');
 PERFORM pv.set_reference ( 'wireless_link.interfaceid', 'mac_interface');
 PERFORM pv.set_reference ( 'wireless_link.otherend', 'wireless_link');
  
 PERFORM pv.set_reference ( 'sip_client.deviceid', 'device');
 
 
 PERFORM pv.set_reference ( 'mac_interface.ipreservationid', 'ip_reservation');
 PERFORM pv.set_reference ( 'mac_interface.deviceid', 'device');
 PERFORM pv.set_reference ( 'mac_interface.ownerid', 'service');
 
 RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pv.set_editors() returns int as $$
BEGIN
 UPDATE pv.field_info SET editor_class = 'Text';
 UPDATE pv.field_info SET editor_class = 'Memo' WHERE type='text';
 UPDATE pv.field_info SET editor_class = 'Boolean' WHERE type='bit';
 UPDATE pv.field_info SET editor_class = 'Time' WHERE type='timestamp';
 PERFORM pv.set_editor_class ( 'field_info.editor_class', 'Radio', NULL );
 RETURN 0;
END;
$$ LANGUAGE plpgsql;

UPDATE pv.object_txt_expressions SET objecttxtexpr = '''['' || subscriberid || ''] '' || name' WHERE objecttype='subscriber';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''['' || typeid || ''] '' || name' WHERE objecttype='type_of_service';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''['' || name || ''] '' || network::text' WHERE objecttype='ip_subnet';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''[TABLE] '' || name' WHERE objecttype='table_info';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''[FIELD] '' || path' WHERE objecttype='field_info';

----------------------------------------------------------------------------------------------------
--
-- database/999finalize.sql
----------------------------------------------------------------------------------------------------
-- $Id$

INSERT INTO pv.table_info (schema, name, label, title, info, txtexpression) 
SELECT n.nspname, c.relname, c.relname, c.relname, 'Table ' || c.relname || '.',
  ote.objecttxtexpr
FROM pg_class c INNER JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pv.object_txt_expressions ote ON ote.objecttype = c.relname
WHERE n.nspname = 'pv' AND c.relkind = 'r'::char ORDER BY c.oid;


INSERT INTO pv.field_info(name, lp, ndims, type, length, classid, label, quickhelp, reference,constraintid)
SELECT att.attname, att.attnum-5, att.attndims, 
    CASE WHEN att.attndims > 0 THEN 'array:' || substring(t.typname from 2) ELSE t.typname END, 
    att.attlen, ac.objectid, att.attname, 
    ac.name || '.' || att.attname || ' : ' || t.typname || '(' ||  att.attlen || ') [' || att.attndims || ']',
    m2.localid, con.oid
   FROM 
    pv.table_info ac INNER JOIN pv.map_class_ids m ON m.localid = ac.objectid
    INNER JOIN pg_attribute att ON att.attrelid = m.systemid
    INNER JOIN pg_type t ON t.oid = att.atttypid
    LEFT JOIN pg_constraint con ON (att.attnum = ANY ( con.conkey ) AND con.conrelid = m.systemid AND con.contype='f'::char)
    LEFT JOIN pv.map_class_ids m2 ON (con.confrelid = m2.systemid)
WHERE    
  att.attnum > 0;

UPDATE pv.table_info t SET superclass = m2.localid FROM pv.table_info ti2, pv.table_info ti, pv.map_class_ids m1, pv.map_class_ids m2, pg_inherits inh WHERE ti.objectid = m1.localid AND m1.systemid = inh.inhrelid AND inh.inhparent = m2.systemid AND ti2.objectid = m2.localid AND t.objectid = m1.localid;
  
SELECT pv.fill_subclass_array ( pv.table_object_id ( 'object' ) );
SELECT pv.propagate_references();
UPDATE pv.field_info SET reference = pv.table_object_id ('object') WHERE reference IS NOT NULL;
SELECT pv.set_all_references();

UPDATE pv.field_info SET 
choices = ARRAY['Text', 'Memo', 'Static', 'Combo', 'Search', 'Time', 'Boolean', 'Radio', 'Inet', 'InetPrefix', 'MAC', 'Spin'] 
WHERE classid = pv.table_object_id('field_info') AND name = 'editor_class';

SELECT pv.set_editors();
SELECT pv.set_all_device_role_triggers();
