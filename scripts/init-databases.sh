#!/bin/sh
# Runs once, the first time the dev database container starts with no data:
# loads the schema into the main database, then creates the test database
# (same name with _test on the end) and loads the same schema there.
set -e
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /schema.sql
createdb -U "$POSTGRES_USER" "${POSTGRES_DB}_test"
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "${POSTGRES_DB}_test" -f /schema.sql
