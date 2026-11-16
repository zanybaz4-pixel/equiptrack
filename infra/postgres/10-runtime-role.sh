#!/usr/bin/env bash
set -euo pipefail
: "${POSTGRES_APP_PASSWORD:?Runtime password is required}"
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=ON_ERROR_STOP=1 --set=app_password="$POSTGRES_APP_PASSWORD" <<'SQL'
CREATE ROLE equiptrack_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
SELECT format('ALTER ROLE equiptrack_app PASSWORD %L', :'app_password') \gexec
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
