drop schema if exists pv cascade;
create schema pv;
SET default_with_oids=TRUE;

----------------------------------------------------------------------------------------------------
--    BASIC OBJECT
----------------------------------------------------------------------------------------------------
create table pv.object_txt_expressions (
  objecttype VARCHAR(64) NOT NULL PRIMARY KEY,
  objecttxtexpr text NOT NULL
);

create table pv.object_search_txt (
  objectid int8 PRIMARY KEY,
  txt varchar(128)
);

create table pv.object (
  objectid SERIAL8,
  objectscope smallint NOT NULL DEFAULT 0,
  objectcreation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  objectmodification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  objectdeletion TIMESTAMP NULL,
  objecttype VARCHAR(64) NOT NULL DEFAULT 'object',
  objecttypeid oid NULL,
  PRIMARY KEY (objectid)
);

CREATE VIEW pv.objecttxt AS SELECT o.*, t.txt as objecttxt FROM pv.object o LEFT JOIN pv.object_search_txt t ON o.objectid = t.objectid;

-- HANDLER CALLED BEFORE ACTION ON OBJECT ROWS
create function pv.handle_object_lifespan_before() RETURNS trigger AS $handle_object_lifespan$
  BEGIN
    IF (TG_OP = 'INSERT') THEN
      NEW.objecttype := TG_TABLE_NAME;
      NEW.objecttypeid := TG_RELID;
      RETURN NEW;      
    END IF;
    
    IF (TG_OP = 'UPDATE') THEN
      NEW.objectmodification := CURRENT_TIMESTAMP;
      RETURN NEW;
    END IF;    
    
    IF (TG_OP = 'DELETE') THEN
      RETURN OLD;
    END IF;
    
  END;
$handle_object_lifespan$ LANGUAGE plpgsql;

-- HANDLER CALLED AFTER ACTION ON OBJECT ROWS
create function pv.handle_object_lifespan_after() RETURNS trigger AS $handle_object_lifespan$
  BEGIN
    IF (TG_OP = 'INSERT') THEN      
      INSERT INTO pv.object_search_txt (objectid, txt) VALUES ( NEW.objectid, pv.obj_txt_repr (NEW.objectid, NEW.objecttype) );
    END IF;
    IF (TG_OP = 'UPDATE') THEN
      UPDATE pv.object_search_txt SET txt = pv.obj_txt_repr (NEW.objectid, NEW.objecttype) WHERE objectid = NEW.objectid;
    END IF;    
    RETURN NEW;      
  END;
$handle_object_lifespan$ LANGUAGE plpgsql;

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

create function pv.obj (objid int8) returns record AS $obj$
  DECLARE
    r RECORD;
    objrow pv.object%ROWTYPE;
  BEGIN
    SELECT * INTO objrow FROM pv.object WHERE objectid = objid;
    EXECUTE 'SELECT * FROM pv.' || objrow.objecttype || ' WHERE objectid = ' || objid INTO r;
    RETURN r;
  END;
$obj$ LANGUAGE plpgsql;

CREATE FUNCTION pv.obj_txt_repr (objid int8, objtype text) returns text as $repr$
  DECLARE
    expr text;
    repr text;
  BEGIN
  SELECT e.objecttxtexpr INTO expr FROM pv.object_txt_expressions e INNER JOIN pv.object o ON o.objecttype = e.objecttype AND o.objectid = objid LIMIT 1;
    EXECUTE 'SELECT ' || expr || ' FROM pv.' || objtype || ' WHERE objectid = ' || objid INTO repr;
    RETURN repr;
  END;
$repr$ LANGUAGE plpgsql;

----------------------------------------------------------------------------------------------------
create table pv.event (
  refobjectid int8 REFERENCES pv.object ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  executedtime timestamp not null default current_timestamp,
  class smallint not null default 0,
  severity smallint not null default 0,
  planned bit not null default '0',
  initiator varchar(32) not null default 'internal',
  data text
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'event' );

create table pv.note (
  refobjectid int8 REFERENCES pv.object ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  username timestamp not null default current_timestamp,
  content text  
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'note' );

----------------------------------------------------------------------------------------------------
--     IP ADDRESSING
----------------------------------------------------------------------------------------------------
create table pv.ip_subnet (
  name varchar(64) not null,
  scope varchar(64) null,  
  designation varchar(64)[] not null default '{service}',
  network cidr not null unique,
  gateway inet null,
  active bit not null default '1',
  allownew bit not null default '1',
  dhcpserver inet null  
) inherits (pv."object");
SELECT pv.setup_object_subtable ('ip_subnet' );

create table pv.ip_reservation (
  ownerid int8 REFERENCES pv.object ON DELETE CASCADE ON UPDATE CASCADE NULL,
  subnetid int8 REFERENCES pv.ip_subnet ON DELETE SET NULL ON UPDATE CASCADE NULL,
  address inet not null unique,
  designation smallint not null default 0,
  dhcp bit not null default '1',
  lastused timestamp null,
  state smallint not null default 0  
) inherits (pv."object");
SELECT pv.setup_object_subtable ('ip_reservation' );

create function pv.check_ip_reservation_uniqueness() returns TRIGGER AS $ip_uniq$
  DECLARE
    addrcnt int;
    subnetid int8;
    cnt int;
  BEGIN
    SELECT count(address) FROM pv.ip_reservation WHERE address >>= NEW.address AND objectid <> NEW.objectid into addrcnt;
    IF (addrcnt > 0) THEN
      RAISE EXCEPTION 'Duplicate IP address reservation requested. ';
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
--     LOCATION
----------------------------------------------------------------------------------------------------
create table pv.city (
  name varchar(64) not null unique,
  handle varchar(16) not null
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'city' );

create table pv.street (
  name varchar(64) not null,
  handle varchar(16) not null,
  cityid int8 REFERENCES pv.city ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  UNIQUE (name, cityid)
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'street' );

create table pv.building (
  number varchar(16) not null,
  handle varchar null,
  streetid int8 REFERENCES pv.street ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'building' );

create table pv.location (
  number varchar(16) not null,
  buildingid int8 REFERENCES pv.building ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  entrance varchar(3) null,
  floor varchar(3) null
) inherits ( pv."object" );
SELECT pv.setup_object_subtable ( 'location' );


----------------------------------------------------------------------------------------------------
--     CLASS_OF_SERVICE
----------------------------------------------------------------------------------------------------
create table pv.class_of_service (
  classid varchar(8) not null unique,
  name varchar(128) not null,
  classparams varchar(64)[][] not null  
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'class_of_service' );

create table pv.type_of_service (
  typeid varchar(8) not null unique,
  name varchar(128) not null,
  classmap int8[] not null  
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'type_of_service' );

----------------------------------------------------------------------------------------------------
--     SUBSCRIBER
----------------------------------------------------------------------------------------------------
create table pv.subscriber (
  subscriberid integer not null unique,
  name varchar(256) not null,  
  postaladdress varchar(512) null,
  email varchar(128)[] null,
  telephone varchar(32)[] null
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'subscriber' );


create table pv.service (
  subscriberid int8 REFERENCES pv.subscriber ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  typeofservice int8 REFERENCES pv.type_of_service ON DELETE SET NULL ON UPDATE CASCADE NOT NULL,
  classofservice int8 REFERENCES pv.class_of_service ON DELETE SET NULL ON UPDATE CASCADE NULL,
  locationid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NOT NULL,
  handle varchar(24) NULL,
  status smallint not null default 1  
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'service' );


--**************************************************************************************************
--|     NETWORK DEVICES 
--vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
----------------------------------------------------------------------------------------------------
--|     DEVICE
----------------------------------------------------------------------------------------------------
create table pv.device (
  name varchar(128) null,
  parentid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,
  ownerid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,
  devicelevel varchar(4) not null,
  devicerole varchar(64)[] null,
  modelid int8 null,
  serialnumber varchar(128) null
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'device' );

----------------------------------------------------------------------------------------------------
--     DEVICE_ROLE
----------------------------------------------------------------------------------------------------
create table pv.device_role (
  deviceid int8 REFERENCES pv.device ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'device_role');

create table pv.docsis_cable_modem (
  cmtsid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,
  downstreamid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,
  upstreamid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,
  customersn varchar(32) NULL,
  maxcpe smallint NOT NULL DEFAULT 1,  
  cpemacfilter bit NOT NULL DEFAULT '0',
  cpeipfilter bit NOT NULL DEFAULT '1',
  netbiosfilter bit NOT NULL DEFAULT '1',
  docsisversion numeric(2,1) NOT NULL DEFAULT 1.0,
  nightsurf bit NULL,
  networkaccess bit NOT NULL DEFAULT '1',
  upgradefilename varchar(128) NULL,
  upgradeserver inet NULL,
  configfilename varchar(128) NULL,    
  cvc int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,
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
  mgmt_pass varchar(16) null  
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ('routeros_device' );

create table pv.nat_router (
  localaddr inet not null,
  dhcp bit not null default '1',
  lanports smallint null
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'nat_router' );

create table pv.wireless (
  essid varchar(128) null,
  bssid macaddr null,
  interfaceid int8 REFERENCES pv.object ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  band varchar(32) null,
  frequency smallint null,
  channelwidth smallint null  
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'wireless' );

create table pv.core_radio_link (
  otherend int8 REFERENCES pv.wireless ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  mode smallint not null default 1
) inherits (pv."wireless");
SELECT pv.setup_object_subtable ( 'core_radio_link' );

create table pv.sip_client (
  server varchar(256) not null,
  account varchar(256) not null,
  pass varchar(256) not null,
  pstn_number varchar(64) not null
) inherits (pv."device_role");
SELECT pv.setup_object_subtable ( 'sip_client' );

----------------------------------------------------------------------------------------------------
--|     INTERFACE
----------------------------------------------------------------------------------------------------
create table pv.mac_interface (
  mac macaddr not null unique,
  ipreservationid int8 REFERENCES pv.ip_reservation ON DELETE SET NULL ON UPDATE CASCADE NULL
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'mac_interface' );

----------------------------------------------------------------------------------------------------
----------------   METADATA   ----------------------------------------------------------------------
----------------------------------------------------------------------------------------------------

CREATE TABLE pv.table_info (
  schema name not null,
  name name not null unique,  
  label varchar(128) null,
  title varchar(128) null,
  info text null,
  pprint_expression text default '#%(objectid)s',
  pk name not null default 'objectid',
  UNIQUE (schema, name)
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'table_info' );


CREATE TABLE pv.field_info (  
  lp smallint not null,
  name name not null,
  path varchar(128) null,
  type name not null,
  ndims smallint not null,
  length smallint null,
  classid int REFERENCES pv.table_info ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  reference int REFERENCES pv.table_info ON DELETE SET NULL ON UPDATE CASCADE NULL,
  reference_editable bit not null default '0',
  pprint_fkexpression text default null,  
  required bit not null default '0',
  label varchar(128) null,
  quickhelp varchar(256) null,
  info text null,
  editor_class name default 'ValueEditor'
) inherits (pv."object");
SELECT pv.setup_object_subtable ( 'field_info' );



CREATE VIEW pv.map_class_ids AS
select c.oid as systemid, ac.objectid as localid 
from pv.table_info ac inner join pg_class c on c.relname = ac.name 
inner join pg_namespace n on n.oid = c.relnamespace 
where n.nspname = ac.schema;

CREATE VIEW pv.reference_info AS
select c1.name || '(' || f1.name || ') REFERENCES ' || c2.name  from 
    pv.table_info c1 INNER JOIN pv.field_info f1 ON f1.classid = c1.objectid 
    INNER JOIN pv.table_info c2 ON c2.objectid = f1.reference 
    WHERE f1.reference is not null;

create function pv.handle_field_info_change() RETURNS trigger AS $body$
  DECLARE
    tname text;
  BEGIN
    IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE') THEN
      SELECT name INTO tname FROM pv.table_info WHERE objectid = NEW.classid;
      NEW.path = tname || '.' || NEW.name;            
      RETURN NEW;      
    END IF;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER set_field_info_path BEFORE UPDATE OR INSERT ON pv.field_info 
FOR EACH ROW EXECUTE PROCEDURE pv.handle_field_info_change();
  
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
  

UPDATE pv.object_txt_expressions SET objecttxtexpr = '''['' || subscriberid || ''] '' || name' WHERE objecttype='subscriber';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''['' || typeid || ''] '' || name' WHERE objecttype='type_of_service';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''['' || name || ''] '' || network::text' WHERE objecttype='ip_subnet';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''[TABLE] '' || name' WHERE objecttype='table_info';
UPDATE pv.object_txt_expressions SET objecttxtexpr = '''[FIELD] '' || path' WHERE objecttype='field_info';

INSERT INTO pv.table_info (schema, name, label, title, info) 
SELECT n.nspname, c.relname, c.relname, c.relname, 'Table ' || c.relname || '.'
FROM pg_class c INNER JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'pv' AND c.relkind = 'r'::char;

INSERT INTO pv.field_info(name, lp, ndims, type, length, classid, label, quickhelp, reference)
SELECT att.attname, att.attnum, att.attndims, 
    CASE WHEN att.attndims > 0 THEN 'array:' || substring(t.typname from 2) ELSE t.typname END, 
    att.attlen, ac.objectid, att.attname, 
    ac.name || '.' || att.attname || ' : ' || t.typname || '(' ||  att.attlen || ') [' || att.attndims || ']',
    m2.localid
   FROM 
    pv.table_info ac INNER JOIN pv.map_class_ids m ON m.localid = ac.objectid
    INNER JOIN pg_attribute att ON att.attrelid = m.systemid
    INNER JOIN pg_type t ON t.oid = att.atttypid
    LEFT JOIN pg_constraint con ON (att.attnum = ANY ( con.conkey ) AND con.conrelid = m.systemid AND con.contype='f'::char)
    LEFT JOIN pv.map_class_ids m2 ON (con.confrelid = m2.systemid)
WHERE    
  att.attnum > 0;


COPY pv.type_of_service(typeid, name,classmap) FROM STDIN DELIMITER '|';
INT/TVC|Dostęp do Internetu w Telewizji Kablowej|{}
INT/RAD|Radiowy dostęp do Internetu|{} 
INT/LAN|Dostęp do Internetu w sieci LAN|{}
INT/BIZ|Korporacyjny Internet|{}
TEL/VOIP|Telefonia VoIP|{}
WIFI|Radiowy Internet w domu|{}
HOST/DOM|Hosting domeny|{}
\.

COPY pv.ip_subnet(name, network) FROM STDIN DELIMITER '|';
network 10/8|10.0.0.0/8
network 10.1/16|10.1.0.0/16
\.

COPY pv.subscriber (subscriberid, name) FROM STDIN DELIMITER '|';
1000|Jan Kowalski
1001|Roman Pawłowski
1002|Paweł Romanowski
\.