-- $Id:$

create table {:SCHEMA:}event (
  refobjectid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  executedtime timestamp not null default current_timestamp,
  class smallint not null default 0,
  severity smallint not null default 0,
  planned bit not null default '0',
  initiator varchar(32) not null default 'internal',
  data text,
  check (refobjectid <> objectid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'event' );

create table {:SCHEMA:}note (
  refobjectid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  timeadded timestamp not null default current_timestamp,
  addedby varchar(64) null,
  content text,
  check (refobjectid <> objectid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'note' );

create table {:SCHEMA:}object_parameter (
  refobjectid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  parametername varchar(64) not null,
  content text not null,
  check (refobjectid <> objectid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'object_parameter' );

create table {:SCHEMA:}object_flag (
  refobjectid int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  flagname varchar(64) not null,
  unique (refobjectid, flagname),
  check (refobjectid <> objectid)
) inherits ( {:SCHEMA:}"object" );
SELECT {:SCHEMA:}setup_object_subtable ( 'object_flag' );

create function {:SCHEMA:}object_has_flag (objid int8, fname varchar) returns boolean AS $obj$
  BEGIN
    SELECT * FROM {:SCHEMA:}object_flag WHERE refobjectid = objid AND upper(flagname) = upper(fname);
    IF NOT FOUND THEN
      RETURN FALSE;
    ELSE
      RETURN TRUE;
    END IF;
  END;
$obj$ LANGUAGE plpgsql;

create function {:SCHEMA:}object_param (objid int8, pname varchar) returns varchar AS $obj$
  DECLARE
    cnt varchar;
  BEGIN
    SELECT content INTO cnt FROM {:SCHEMA:}object_parameter WHERE refobjectid = objid 
    AND upper(parametername) = upper(pname);
    IF NOT FOUND THEN
      RETURN NULL;
    ELSE
      RETURN cnt;
    END IF;
  END;
$obj$ LANGUAGE plpgsql;

