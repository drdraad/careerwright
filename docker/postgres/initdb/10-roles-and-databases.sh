#!/usr/bin/env bash
# Runs once, when the data volume is first initialised. Creates the application and DBOS
# system databases, each owned by a migration role, plus the non-owner runtime roles
# (ADR 0002 decision 2). Passwords are read from Compose secret files inside psql, never
# passed as command arguments or environment variables.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres <<'SQL'
\set migrator_password `cat /run/secrets/pg_migrator`
\set api_password `cat /run/secrets/pg_api`
\set worker_password `cat /run/secrets/pg_worker`
\set dbos_owner_password `cat /run/secrets/pg_dbos_owner`
\set dbos_runtime_password `cat /run/secrets/pg_dbos_runtime`

CREATE ROLE careerwright_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
    PASSWORD :'migrator_password';
CREATE ROLE careerwright_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT
    PASSWORD :'api_password';
CREATE ROLE careerwright_worker LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT
    PASSWORD :'worker_password';
CREATE ROLE careerwright_dbos_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
    PASSWORD :'dbos_owner_password';
CREATE ROLE careerwright_dbos_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT
    PASSWORD :'dbos_runtime_password';

CREATE DATABASE careerwright_app OWNER careerwright_migrator;
CREATE DATABASE careerwright_dbos OWNER careerwright_dbos_owner;
REVOKE ALL ON DATABASE careerwright_app FROM PUBLIC;
REVOKE ALL ON DATABASE careerwright_dbos FROM PUBLIC;
GRANT CONNECT ON DATABASE careerwright_app TO careerwright_migrator, careerwright_api, careerwright_worker;
GRANT CONNECT ON DATABASE careerwright_dbos TO careerwright_dbos_owner, careerwright_dbos_runtime;

\connect careerwright_app
REVOKE ALL ON SCHEMA public FROM PUBLIC;
\connect careerwright_dbos
REVOKE ALL ON SCHEMA public FROM PUBLIC;
SQL
