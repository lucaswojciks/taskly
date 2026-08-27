#!/bin/bash
# Runs once, on first initialization of the Postgres data directory.
# Creates the isolated database used by the test suite.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE taskly_test;
    GRANT ALL PRIVILEGES ON DATABASE taskly_test TO "$POSTGRES_USER";
EOSQL
