-- $Id$

INSERT INTO {:SCHEMA:}table_info (schema, name, label, title, info, txtexpression) 
SELECT n.nspname, c.relname, c.relname, c.relname, 'Table ' || c.relname || '.',
  ote.objecttxtexpr
FROM pg_class c INNER JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN {:SCHEMA:}object_txt_expressions ote ON ote.objecttype = c.relname
WHERE n.nspname = 'pv' AND c.relkind = 'r'::char ORDER BY c.oid;


INSERT INTO {:SCHEMA:}field_info(name, lp, ndims, type, length, classid, label, quickhelp, reference,constraintid)
SELECT att.attname, att.attnum-5, att.attndims, 
    CASE WHEN att.attndims > 0 THEN 'array:' || substring(t.typname from 2) ELSE t.typname END, 
    att.attlen, ac.objectid, att.attname, 
    ac.name || '.' || att.attname || ' : ' || t.typname || '(' ||  att.attlen || ') [' || att.attndims || ']',
    m2.localid, con.oid
   FROM 
    {:SCHEMA:}table_info ac INNER JOIN {:SCHEMA:}map_class_ids m ON m.localid = ac.objectid
    INNER JOIN pg_attribute att ON att.attrelid = m.systemid
    INNER JOIN pg_type t ON t.oid = att.atttypid
    LEFT JOIN pg_constraint con ON (att.attnum = ANY ( con.conkey ) AND con.conrelid = m.systemid AND con.contype='f'::char)
    LEFT JOIN {:SCHEMA:}map_class_ids m2 ON (con.confrelid = m2.systemid)
WHERE    
  att.attnum > 0;

UPDATE {:SCHEMA:}table_info t SET superclass = m2.localid FROM {:SCHEMA:}table_info ti2, {:SCHEMA:}table_info ti, {:SCHEMA:}map_class_ids m1, {:SCHEMA:}map_class_ids m2, pg_inherits inh WHERE ti.objectid = m1.localid AND m1.systemid = inh.inhrelid AND inh.inhparent = m2.systemid AND ti2.objectid = m2.localid AND t.objectid = m1.localid;
  
SELECT {:SCHEMA:}fill_subclass_array ( {:SCHEMA:}table_object_id ( 'object' ) );
SELECT {:SCHEMA:}propagate_references();
UPDATE {:SCHEMA:}field_info SET reference = {:SCHEMA:}table_object_id ('object') WHERE reference IS NOT NULL;
SELECT {:SCHEMA:}set_all_references();

UPDATE {:SCHEMA:}field_info SET 
choices = ARRAY['Text', 'Memo', 'Static', 'Combo', 'Search', 'Time', 'Boolean', 'Radio', 'Inet', 'InetPrefix', 'MAC', 'Spin'] 
WHERE classid = {:SCHEMA:}table_object_id('field_info') AND name = 'editor_class';

SELECT {:SCHEMA:}set_editors();
SELECT {:SCHEMA:}set_all_device_role_triggers();
