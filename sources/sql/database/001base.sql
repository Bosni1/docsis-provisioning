-- $Id:$

--
-- This is the table to which all references are actually made.
--
create table {:SCHEMA:}objectids (
  objectid int8 primary key
);
create index idx_objectids_objectid on {:SCHEMA:}objectids (objectid);

--
-- Objects' textual representations are kept here
--
create table {:SCHEMA:}object_search_txt (
  objectid int8 PRIMARY KEY,
  txt varchar(128)
);
create index object_search_txt_objectid on {:SCHEMA:}object_search_txt (objectid);

--
-- Expressions used to generate objects' text representations.
--
create table {:SCHEMA:}object_txt_expressions (
  objecttype name NOT NULL PRIMARY KEY,
  objecttxtexpr text NOT NULL
);
create index idx_object_txt_expr_objecttype on {:SCHEMA:}object_txt_expressions (objecttype);

--
-- Change object_search_txt when txt_expression changes.
--
create function {:SCHEMA:}object_txt_expression_change() RETURNS trigger AS $body$  
  BEGIN
    IF (NEW.objecttxtexpr <> OLD.objecttxtexpr) THEN
      UPDATE {:SCHEMA:}object_search_txt AS ost SET 
        txt = {:SCHEMA:}obj_txt_repr ( ost.objectid::int8, o.objecttype::name ) 
        FROM {:SCHEMA:}object o WHERE o.objectid = ost.objectid AND o.objecttype = NEW.objecttype;
    END IF;    
    RETURN NEW;
  END;
$body$ LANGUAGE plpgsql;
CREATE TRIGGER bulk_update_txt_expressions AFTER UPDATE ON {:SCHEMA:}object_txt_expressions
FOR EACH ROW EXECUTE PROCEDURE {:SCHEMA:}object_txt_expression_change();


--
-- Base table.
--
create table {:SCHEMA:}object (
  objectid SERIAL8,
  objectscope smallint NOT NULL DEFAULT 0,
  objectcreation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  objectmodification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  
  objecttype name NOT NULL DEFAULT 'object',
  PRIMARY KEY (objectid)
);
CREATE VIEW {:SCHEMA:}objecttxt AS SELECT o.*, t.txt as objecttxt 
    FROM {:SCHEMA:}object o LEFT JOIN {:SCHEMA:}object_search_txt t ON o.objectid = t.objectid;

-- HANDLER CALLED BEFORE ACTION ON OBJECT ROWS
-- on insert: insert objectis into "objectids", set objecttype
-- on update: set object modification time
-- on delete: delete from "objectids"
create function {:SCHEMA:}handle_object_lifespan_before() RETURNS trigger AS $handle_object_lifespan$
  BEGIN
    IF (TG_OP = 'INSERT') THEN
      INSERT INTO {:SCHEMA:}objectids VALUES (NEW.objectid);
      NEW.objecttype := TG_TABLE_NAME;
      RETURN NEW;      
    END IF;
    
    IF (TG_OP = 'UPDATE') THEN
      NEW.objectmodification := CURRENT_TIMESTAMP;
      RETURN NEW;
    END IF;    
    
    IF (TG_OP = 'DELETE') THEN
      DELETE FROM {:SCHEMA:}objectids WHERE objectid = OLD.objectid;
      RETURN OLD;
    END IF;
    
  END;
$handle_object_lifespan$ LANGUAGE plpgsql;



-- HANDLER CALLED AFTER ACTION ON OBJECT ROWS
-- on insert: set object_search_txt
-- on update: update object_search_txt
create function {:SCHEMA:}handle_object_lifespan_after() RETURNS trigger AS $handle_object_lifespan$
  BEGIN
    IF (TG_OP = 'INSERT') THEN      
      INSERT INTO {:SCHEMA:}object_search_txt (objectid, txt) VALUES ( NEW.objectid, {:SCHEMA:}obj_txt_repr (NEW.objectid, NEW.objecttype) );
    END IF;
    IF (TG_OP = 'UPDATE') THEN
      UPDATE {:SCHEMA:}object_search_txt SET txt = {:SCHEMA:}obj_txt_repr (NEW.objectid, NEW.objecttype) WHERE objectid = NEW.objectid;
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
create function {:SCHEMA:}setup_object_subtable (classname text) returns text as $setup$
  DECLARE
    triggername text;    
  BEGIN
    triggername := 'object_' || classname || '_creation_';
    EXECUTE 'CREATE TRIGGER ' || quote_ident(triggername || '_bf') 
        || ' BEFORE INSERT OR UPDATE OR DELETE ON {:SCHEMA:}' || classname || ' FOR EACH ROW EXECUTE PROCEDURE '
        || ' {:SCHEMA:}handle_object_lifespan_before();';
    EXECUTE 'CREATE TRIGGER ' || quote_ident(triggername || '_af') 
        || ' AFTER INSERT OR UPDATE OR DELETE ON {:SCHEMA:}' || classname || ' FOR EACH ROW EXECUTE PROCEDURE '
        || ' {:SCHEMA:}handle_object_lifespan_after();';
    EXECUTE 'ALTER TABLE {:SCHEMA:}' || classname || ' ADD PRIMARY KEY (objectid)';
    EXECUTE 'INSERT INTO {:SCHEMA:}object_txt_expressions (objecttype, objecttxtexpr) VALUES ( ''' || classname || ''', ''objecttype || objectid'' )';
--    EXECUTE 'ALTER TABLE {:SCHEMA:}' || classname || ' ADD UNIQUE (objectid)';
    RETURN classname || ' triggers are set.';
  END;
$setup$ LANGUAGE plpgsql;

--
--  return text representation for an object
--
CREATE FUNCTION {:SCHEMA:}obj_txt_repr (objid int8, objtype name) returns text as $repr$
  DECLARE
    expr text;
    repr text;
  BEGIN
    SELECT e.objecttxtexpr INTO expr FROM {:SCHEMA:}object_txt_expressions e INNER JOIN {:SCHEMA:}object o ON o.objecttype = e.objecttype AND o.objectid = objid LIMIT 1;  
    IF NOT FOUND THEN 
      RETURN '<null>';
    END IF;
    EXECUTE 'SELECT ' || expr || ' FROM {:SCHEMA:}' || objtype || ' WHERE objectid = ' || objid INTO repr;
    RETURN repr;
  END;
$repr$ LANGUAGE plpgsql;

create function {:SCHEMA:}update_search_txt(objtype name) RETURNS BOoLEAn AS $body$  
  BEGIN
      UPDATE {:SCHEMA:}object_search_txt AS ost SET 
        txt = {:SCHEMA:}obj_txt_repr ( ost.objectid::int8, o.objecttype::name ) 
        FROM {:SCHEMA:}object o WHERE o.objectid = ost.objectid AND o.objecttype = objtype;    
      return TRUE;  
  END;
$body$ LANGUAGE plpgsql;

create function {:SCHEMA:}get_search_txt(objid int8) RETURNS varchar AS $body$  
  declare
  r varchar;
  BEGIN
      SELECT txt INTO r FROM {:SCHEMA:}object_search_txt  WHERE objectid = objid;
      return r;  
  END;
$body$ LANGUAGE plpgsql;

