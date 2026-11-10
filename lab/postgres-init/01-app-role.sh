#!/bin/sh
# WPMgr — provision the unprivileged application login role on first DB init.
set -eu

APP_USER="${WPMGR_DB_APP_USER:-wpmgr_app}"
APP_PASSWORD="${WPMGR_DB_APP_PASSWORD:-wpmgr-app-dev-secret}"
DB_NAME="${POSTGRES_DB:-wpmgr}"

echo "[wpmgr-init] ensuring unprivileged app role '${APP_USER}' on db '${DB_NAME}'"

psql -v ON_ERROR_STOP=1 \
     --username "${POSTGRES_USER}" \
     --dbname "${DB_NAME}" \
     --set=app_user="${APP_USER}" \
     --set=app_password="${APP_PASSWORD}" <<'EOSQL'
SELECT set_config('wpmgr.app_user',     :'app_user',     false);
SELECT set_config('wpmgr.app_password', :'app_password', false);

DO $$
DECLARE
    v_user text := current_setting('wpmgr.app_user');
    v_pass text := current_setting('wpmgr.app_password');
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_user) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE INHERIT',
            v_user, v_pass
        );
        RAISE NOTICE 'created role %', v_user;
    ELSE
        EXECUTE format(
            'ALTER ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS',
            v_user, v_pass
        );
        RAISE NOTICE 'role % already existed; reconciled login/attrs', v_user;
    END IF;
END
$$;
EOSQL

psql -v ON_ERROR_STOP=1 \
     --username "${POSTGRES_USER}" \
     --dbname "${DB_NAME}" \
     -c "GRANT CONNECT ON DATABASE \"${DB_NAME}\" TO \"${APP_USER}\";"

echo "[wpmgr-init] app role '${APP_USER}' ready (LOGIN, NOSUPERUSER, NOBYPASSRLS)"
