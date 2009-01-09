-- $Id:$
create table {:SCHEMA:}device_role (
  deviceid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'device_role');

create table {:SCHEMA:}docsis_cable_modem (
  cmtsid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  downstreamid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  upstreamid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  customersn varchar(32) NULL,
  maxcpe smallint NOT NULL DEFAULT 1,  
  cpemacfilter bit NOT NULL DEFAULT '0',
  cpeipfilter bit NOT NULL DEFAULT '1',
  netbiosfilter bit NOT NULL DEFAULT '1',
  docsisversion numeric(2,2) NOT NULL DEFAULT 1.00,
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
  mgmt_pass varchar(16) null  
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ('routeros_device' );

create table {:SCHEMA:}nat_router (
  localaddr inet not null,
  dhcp bit not null default '1',
  lanports smallint null
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'nat_router' );

create table {:SCHEMA:}wireless (
  essid varchar(128) null,
  bssid macaddr null,
  interfaceid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  band varchar(32) null,
  frequency smallint null,
  channelwidth smallint null
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'wireless' );

create table {:SCHEMA:}core_radio_link (
  otherend int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,  
  mode smallint not null default 1
) inherits ({:SCHEMA:}"wireless");
SELECT {:SCHEMA:}setup_object_subtable ( 'core_radio_link' );

create table {:SCHEMA:}sip_client (
  server varchar(256) not null,
  account varchar(256) not null,
  pass varchar(256) not null,
  pstn_number varchar(64) not null
) inherits ({:SCHEMA:}"device_role");
SELECT {:SCHEMA:}setup_object_subtable ( 'sip_client' );
