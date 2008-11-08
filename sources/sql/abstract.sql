DROP SCHEMA IF EXISTS abstract CASCADE;
CREATE SCHEMA abstract;

CREATE TABLE abstract.class (
  id serial PRIMARY KEY,
  schema name not null,
  name name not null unique,  
  label varchar(128) null,
  title varchar(128) null,
  info text null,
  pprint_expression text default '#%(objectid)s',
  pk name not null default 'objectid',
  UNIQUE (schema, name)
);

CREATE TABLE abstract.field (
  id serial PRIMARY KEY,
  lp smallint not null,
  name name not null,
  type name not null,
  ndims smallint not null,
  length smallint null,
  classid int REFERENCES abstract.class ON DELETE CASCADE ON UPDATE CASCADE NOT NULL,
  reference int REFERENCES abstract.class ON DELETE SET NULL ON UPDATE CASCADE NULL,
  pprint_fkexpression text default null,  
  required bit not null default '0',
  label varchar(128) null,
  quickhelp varchar(256) null,
  info text null
);

CREATE VIEW map_class_ids AS
select c.oid as systemid, ac.id as localid 
from abstract.class ac inner join pg_class c on c.relname = ac.name 
inner join pg_namespace n on n.oid = c.relnamespace 
where n.nspname = ac.schema;

INSERT INTO abstract.class (schema, name, label, title, info) 
SELECT n.nspname, c.relname, c.relname, c.relname, 'Table ' || c.relname || '.'
FROM pg_class c INNER JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'pv' AND c.relkind = 'r'::char;

INSERT INTO abstract.field(name, lp, ndims, type, length, classid, label, quickhelp)
SELECT att.attname, att.attnum, att.attndims, CASE WHEN att.attndims > 0 THEN 'array:' || substring(t.typname from 2) ELSE t.typname END, att.attlen, ac.id, att.attname, 
    ac.name || '.' || att.attname || ' : ' || t.typname || '(' ||  att.attlen || ') [' || att.attndims || ']'
   FROM 
    abstract.class ac INNER JOIN map_class_ids m ON m.localid = ac.id
    INNER JOIN pg_attribute att ON att.attrelid = m.systemid
    INNER JOIN pg_type t ON t.oid = att.atttypid
WHERE    
  att.attnum > 0;
