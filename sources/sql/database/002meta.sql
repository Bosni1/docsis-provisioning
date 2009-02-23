-- $Id:$

--
-- Table information used by GUI
--
CREATE TABLE {:SCHEMA:}table_info (
  schema name not null,
  name name not null unique,  
  superclass int8 REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
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
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'table_info' );


--
-- Table column information used by GUI
--
CREATE TABLE {:SCHEMA:}field_info (  
  lp smallint not null,
  name name not null,
  path varchar(128) null,
  type name not null,
  ndims smallint not null,
  length smallint null,
  classid int REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  reference int REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
  arrayof int REFERENCES {:SCHEMA:}objectids ON DELETE SET NULL ON UPDATE CASCADE NULL,
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
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'field_info' );

--
-- Table column information used by GUI
--
CREATE TABLE {:SCHEMA:}mtm_relationship (  
  mtm_table_name name not null,
  relationship_name name not null,
  table_1 name not null,
  table_1_handle name not null,
  table_2 name not null,
  table_2_handle name not null,
  unique (table_1, table_1_handle),
  unique (table_2, table_2_handle),
  unique (relationship_name)
) inherits ({:SCHEMA:}"object");
SELECT {:SCHEMA:}setup_object_subtable ( 'mtm_relationship' );

CREATE VIEW {:SCHEMA:}map_class_ids AS
select c.oid as systemid, ac.objectid as localid 
from {:SCHEMA:}table_info ac inner join pg_class c on c.relname = ac.name 
inner join pg_namespace n on n.oid = c.relnamespace 
where n.nspname = ac.schema;

CREATE VIEW {:SCHEMA:}reference_info AS
select 'PERFORM {:SCHEMA:}set_reference ( ''' || c1.name || '.' || f1.name || ''', ''' || c2.name || ''');'  from 
    {:SCHEMA:}table_info c1 INNER JOIN {:SCHEMA:}field_info f1 ON f1.classid = c1.objectid 
    INNER JOIN {:SCHEMA:}table_info c2 ON c2.objectid = f1.reference 
    WHERE f1.reference is not null;

CREATE VIEW {:SCHEMA:}all_references AS
select c1.objectid as reftableid, c1.name as reftable,  f1.name as refcolumn, f1.constraintid as refcon from 
    {:SCHEMA:}table_info c1 INNER JOIN {:SCHEMA:}field_info f1 ON f1.classid = c1.objectid 
    INNER JOIN {:SCHEMA:}table_info c2 ON c2.objectid = f1.reference 
    WHERE f1.reference is not null;

-- create table {:SCHEMA:}x ( x text );
create function {:SCHEMA:}handle_field_info_change() RETURNS trigger AS $body$
  DECLARE
    tname text;
    mytable RECORD;
    subf RECORD;
  BEGIN
    IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE') THEN
      SELECT name INTO tname FROM {:SCHEMA:}table_info WHERE objectid = NEW.classid;      
      NEW.path = tname || '.' || NEW.name;            
      IF (TG_OP = 'UPDATE') THEN
        SELECT * INTO mytable FROM {:SCHEMA:}table_info WHERE objectid = NEW.classid;
        IF (NEW.reference <> OLD.reference) THEN          
--          INSERT INTO {:SCHEMA:}x VALUES ( mytable.name || ' ' || NEW.name );
--          FOR subf IN SELECT f.* FROM {:SCHEMA:}field_info f, {:SCHEMA:}table_info t 
--            WHERE t.objectid = ANY ( mytable.subclasses) AND f.classid = t.objectid AND
--            f.
          UPDATE {:SCHEMA:}field_info f SET reference = NEW.reference 
            FROM {:SCHEMA:}table_info t WHERE t.objectid = ANY ( mytable.subclasses ) AND
            f.name = NEW.name AND f.classid = t.objectid;
        END IF;
      END IF;
      RETURN NEW;      
    END IF;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER set_field_info_path BEFORE UPDATE OR INSERT ON {:SCHEMA:}field_info 
FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}handle_field_info_change();

CREATE FUNCTION {:SCHEMA:}table_object_id ( tblname name ) returns int8 as $$
DECLARE
  id int8;
BEGIN
  SELECT objectid INTO id FROM {:SCHEMA:}table_info WHERE name = tblname LIMIT 1;
  RETURN id;
END;
$$ LANGUAGE plpgsql;

--
-- Set the subclasses array in each table_info record, starting at "tableobjectid" and proceeding
-- recursively through the inheritance tree.
--
CREATE FUNCTION {:SCHEMA:}fill_subclass_array ( tableobjectid int8 ) returns int as $$
DECLARE
  tbl RECORD;
  tbl2 RECORD;
BEGIN
  UPDATE {:SCHEMA:}table_info SET subclasses = '{}' WHERE objectid = tableobjectid;
  FOR tbl IN SELECT * FROM {:SCHEMA:}table_info WHERE superclass = tableobjectid LOOP
    PERFORM {:SCHEMA:}fill_subclass_array ( tbl.objectid );
    SELECT * INTO tbl2 FROM {:SCHEMA:}table_info WHERE objectid = tbl.objectid;
    UPDATE {:SCHEMA:}table_info SET subclasses = array_cat (subclasses, array_append(tbl2.subclasses, tbl2.objectid)) WHERE objectid = tableobjectid;
  END LOOP;
  RETURN 1;
END;
$$ LANGUAGE plpgsql;


create function {:SCHEMA:}handle_table_info_change() RETURNS trigger AS $body$
  DECLARE
    tname text;
  BEGIN
    IF (NEW.txtexpression <> OLD.txtexpression) THEN
      UPDATE {:SCHEMA:}object_txt_expressions SET objecttxtexpr = NEW.txtexpression WHERE objecttype = NEW.name;      
    END IF;    
    RETURN NEW;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER set_table_info BEFORE UPDATE ON {:SCHEMA:}table_info 
FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}handle_table_info_change();

--
--  Since references are not automatically inherited, we do it manually.
--
CREATE FUNCTION {:SCHEMA:}propagate_references () returns int as $$
DECLARE
  refs RECORD;
  child RECORD;
  stbl RECORD;
  con RECORD;
  cmd text;
BEGIN
  FOR refs IN SELECT * FROM {:SCHEMA:}all_references LOOP
    SELECT * INTO stbl FROM ONLY {:SCHEMA:}table_info WHERE objectid = refs.reftableid;
    FOR child IN SELECT * FROM {:SCHEMA:}table_info WHERE objectid = ANY ( stbl.subclasses ) LOOP
      cmd := 'ALTER TABLE {:SCHEMA:}' || child.name || ' ADD  FOREIGN KEY (' || refs.refcolumn || ') REFERENCES {:SCHEMA:}objectids ';
      SELECT * INTO con FROM pg_constraint WHERE oid = refs.refcon;                       
      
      cmd := cmd || {:SCHEMA:}constraint_construct ( 'DELETE', con.confdeltype );
      cmd := cmd || ' ' || {:SCHEMA:}constraint_construct ( 'UPDATE', con.confupdtype );
      EXECUTE cmd;               
      -- insert into {:SCHEMA:}x values (cmd);      
      cmd := 'UPDATE {:SCHEMA:}field_info SET reference = {:SCHEMA:}table_object_id (''object'') WHERE path = ''' || child.name || '.' || refs.refcolumn || '''';
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
CREATE FUNCTION {:SCHEMA:}set_reference ( field text, tbl text) returns int as $$
DECLARE
  idx_tbl varchar;
  idx_col varchar;
BEGIN
  idx_tbl := substr(field, 0, strpos(field, '.')) ; 
  idx_col := substr(field, strpos(field, '.')+1);
  UPDATE {:SCHEMA:}field_info SET reference = {:SCHEMA:}table_object_id ( tbl ) WHERE path = field;
  EXECUTE 'CREATE INDEX idx_ref_' || tbl  || '_' || replace(field,'.','_') || ' ON {:SCHEMA:}' || idx_tbl
  || ' ( ' || idx_col || ' ) '; 
  RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION {:SCHEMA:}set_editor_class ( field text, editor text, params varchar[]) returns int as $$
BEGIN
  UPDATE {:SCHEMA:}field_info SET editor_class = editor, editor_class_params = params  
  WHERE path = field;
  RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION {:SCHEMA:}constraint_construct ( ev text, t text) returns text as $$
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


CREATE FUNCTION {:SCHEMA:}create_mtm_relationship ( t1 name, t2 name, rname name) returns text as $$
DECLARE
  tname name;
BEGIN
  tname = '_mtm_' || rname || '_' || t1 || '_' || t2;
  EXECUTE 'CREATE TABLE {:SCHEMA:}' || tname || ' ( ' ||
  ' refobjectid1 int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, ' ||
  ' refobjectid2 int8 REFERENCES {:SCHEMA:}objectids ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, ' ||
  ' refdata int8 NULL, ' ||
  ' PRIMARY KEY (refobjectid1, refobjectid2) ' ||
  ' ) ';
  INSERT INTO {:SCHEMA:}mtm_relationship (mtm_table_name, relationship_name, 
    table_1, table_1_handle, 
    table_2, table_2_handle)
    VALUES (tname, rname, t1, rname, t2, rname);
  return tname;  
END;
$$ LANGUAGE plpgsql;

SELECT {:SCHEMA:}create_mtm_relationship ( 'device', 'service', 'service_device' );


