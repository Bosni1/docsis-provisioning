-- $Id:$

create table {:SCHEMA:}ip_subnet (
  subnetgroupid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  name varchar(64) not null,
  scope varchar(64) null,  
  designation smallint[] not null default '{1}',
  network cidr not null unique,
  gateway inet null,
  active bit not null default '1',
  allownew bit not null default '1',
  dhcpserver inet null  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ('ip_subnet' );

create function {:SCHEMA:}update_ip_reservations_subnet() returns TRIGGER AS $trig$
DECLARE
   subnet_network cidr;
BEGIN  
  IF (TG_OP = 'UPDATE') OR (TG_OP = 'INSERT') THEN
    subnet_network = NEW.network;
  END IF;
  IF (TG_OP = 'DELETE') THEN
    subnet_network = OLD.network;  
  END IF;
  
  UPDATE {:SCHEMA:}ip_reservation ip SET 
  subnetid = (SELECT objectid FROM {:SCHEMA:}ip_subnet WHERE network >> ip.address ORDER BY masklen(network) DESC LIMIT 1 )
  WHERE ip.address << subnet_network;
  IF (TG_OP = 'UPDATE') OR (TG_OP = 'INSERT') THEN
    RETURN NEW;
  END IF;
  IF (TG_OP = 'DELETE') THEN
    RETURN OLD;
  END IF;
END;
$trig$ language plpgsql;
CREATE TRIGGER ip_subnet_on_update_reservations AFTER INSERT OR UPDATE OR DELETE ON {:SCHEMA:}ip_subnet
  FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}update_ip_reservations_subnet();

create table {:SCHEMA:}ip_subnet_group (
  name varchar(64) not null,
  info text null
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ('ip_subnet_group' );

create table {:SCHEMA:}ip_reservation (
  ownerid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NULL,
  subnetid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  interfaceid int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  address inet not null unique,
  designation smallint not null default 1,
  scope smallint not null default 1,
  dhcp bit not null default '1',
  lastused timestamp null,
  state smallint not null default 1  
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ('ip_reservation' );

create function {:SCHEMA:}check_ip_reservation_uniqueness() returns TRIGGER AS $ip_uniq$
  DECLARE
    addrcnt int;
    subnetid int8;
    cnt int;
  BEGIN
    SELECT count(address) FROM {:SCHEMA:}ip_reservation WHERE address >>= NEW.address AND objectid <> NEW.objectid AND designation = NEW.designation into addrcnt;
    IF (addrcnt > 0) THEN
      RAISE EXCEPTION 'Duplicate IP address reservation requested. (designation: ' || NEW.designation || ')';
    END IF;    
    SELECT "objectid" FROM {:SCHEMA:}ip_subnet WHERE network >> NEW.address ORDER BY masklen(network) DESC LIMIT 1 INTO subnetid;
    GET DIAGNOSTICS cnt = ROW_COUNT;
    IF (cnt > 0) THEN 
      NEW.subnetid = subnetid;
    ELSE
      NEW.subnetid = NULL;
    END IF;
    RETURN NEW;
  END;
$ip_uniq$ language plpgsql;
CREATE TRIGGER ip_reservation_uniqueness_check BEFORE INSERT OR UPDATE ON {:SCHEMA:}ip_reservation 
  FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}check_ip_reservation_uniqueness();
