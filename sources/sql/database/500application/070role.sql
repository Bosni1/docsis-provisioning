-- $Id:$
create table {:SCHEMA:}device_role (
  deviceid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'device_role');

create table {:SCHEMA:}cpe (
  macid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  name varchar(32) null,
  info text null,
  os varchar(32) null,
  UNIQUE (macid)
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'cpe');

create table {:SCHEMA:}docsis_cable_modem (
  cmtsid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  downstreamid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  upstreamid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  hfcmacid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NOT NULL,
  usbmacid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  lanmacid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  mgmtmacid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
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
  cvc int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  vendoroptions bytea NULL,
  VENDOR varchar(128) NULL ,
  HW_REV varchar(128) NULL,
  SW_REV varchar(128) NULL,
  MODEL varchar(128) NULL,
  BOOTR varchar(128) NULL,
  BASECAP varchar(128) NULL
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ('docsis_cable_modem' );

create table {:SCHEMA:}routeros_device (
  swmajor smallint null,
  swminor smallint null,
  mgmt_user varchar(16) null,
  mgmt_pass varchar(16) null,
  configuration text null
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ('routeros_device' );

create table {:SCHEMA:}core_switch (
  ports smallint not null default 8
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ('core_switch' );

create table {:SCHEMA:}core_switch_port (
  switchid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  portid int not null,
  portname varchar(16) null,
  linkedto int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  UNIQUE (switchid, portid)
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ('core_switch_port' );

create table {:SCHEMA:}core_router (
  dhcp_relay bit not null default '0',
  default_nexthop inet null
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'core_router' );

create table {:SCHEMA:}core_router_bridged_network (
  routerid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  subnetid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NULL
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'core_router_bridged_network' );

create table {:SCHEMA:}nat_router (
  localaddr inet not null,
  dhcp bit not null default '1',
  lanports smallint null,
  wanmacid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NULL
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'nat_router' );

create table {:SCHEMA:}wireless (
  interfaceid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  band varchar(32) null,
  frequency smallint null,
  channelwidth smallint null,
  UNIQUE (interfaceid)
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'wireless' );

create table {:SCHEMA:}wireless_client (
  accesspointid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  networkaccess bit not null default '1'
) inherits ({:SCHEMA:}"wireless");
SELECT {:SCHEMA:}setup_object_subtable ( 'wireless_client' );
-- on update (insert): if network access changed and accesspoint set - update acl of accesspoint
-- on delete: remove from acl of accesspoint

create table {:SCHEMA:}wireless_ap (
  essid varchar(128) null,
  acl macaddr[] null
) inherits ({:SCHEMA:}"wireless");
SELECT {:SCHEMA:}setup_object_subtable ( 'wireless_ap' );

create table {:SCHEMA:}wireless_link (
  otherend int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  mode smallint not null default 1
) inherits ({:SCHEMA:}"wireless");
SELECT {:SCHEMA:}setup_object_subtable ( 'wireless_link' );

create table {:SCHEMA:}sip_client (
  server varchar(256) not null,
  account varchar(256) not null,
  pass varchar(256) not null,
  pstn_number varchar(64) not null
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'sip_client' );

create function {:SCHEMA:}handle_all_device_role_change() RETURNS trigger AS $body$
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
  UPDATE {:SCHEMA:}object_search_txt SET txt = {:SCHEMA:}obj_txt_repr ( deviceid, 'device' ) WHERE
      objectid = deviceid;
  IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE') THEN
    RETURN NEW;
  ELSIF (TG_OP = 'DELETE') THEN
    RETURN OLD;
  END IF;
  END;
$body$ LANGUAGE plpgsql;

create function {:SCHEMA:}set_all_device_role_triggers() RETURNS void AS $body$
DECLARE
   device_role RECORD;
   trigger_cmd text;
BEGIN
   FOR device_role IN select tc.* from pv.table_info tc, pv.table_info tp where tc.objectid = ANY( tp.subclasses ) AND tp.name = 'device_role' LOOP
      trigger_cmd := 'CREATE TRIGGER update_parent_device_name_' || device_role.name || 
        ' AFTER UPDATE OR INSERT OR DELETE ON {:SCHEMA:}' || device_role.name || 
        ' FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}handle_all_device_role_change();';      
      EXECUTE trigger_cmd;
   END LOOP;
END;
$body$ LANGUAGE plpgsql;


-- CREATE TRIGGER set_field_info_path AFTER UPDATE OR INSERT OR DELETE ON {:SCHEMA:}
-- FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}handle_field_info_change();

