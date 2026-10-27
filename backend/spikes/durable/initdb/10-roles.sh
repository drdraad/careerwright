#!/usr/bin/env bash
# Separate application and DBOS system databases, each with its own role. The passwords are
# read from the environment inside psql (\getenv), never passed as command arguments.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username postgres <<'SQL'
\getenv app_password NESSA_SPIKE_APP_PASSWORD
\getenv dbos_password NESSA_SPIKE_DBOS_PASSWORD
CREATE ROLE nessa_spike_app LOGIN PASSWORD :'app_password';
CREATE ROLE nessa_spike_dbos LOGIN PASSWORD :'dbos_password';
CREATE DATABASE nessa_spike_app OWNER nessa_spike_app;
CREATE DATABASE nessa_spike_dbos OWNER nessa_spike_dbos;
REVOKE ALL ON DATABASE nessa_spike_app FROM PUBLIC;
REVOKE ALL ON DATABASE nessa_spike_dbos FROM PUBLIC;
GRANT CONNECT ON DATABASE nessa_spike_app TO nessa_spike_app;
GRANT CONNECT ON DATABASE nessa_spike_dbos TO nessa_spike_dbos;
SQL
