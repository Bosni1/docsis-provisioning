-- $Id:$
drop schema if exists {:SCHEMA_NAME:} cascade;
create schema {:SCHEMA_NAME:};
create language plpgsql;

SET default_with_oids=TRUE;
