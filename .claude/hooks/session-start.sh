#!/bin/bash
# SessionStart hook (Claude Code on the web): tools the tests need in a fresh cloud container.
# Idempotent and non-interactive. Local machines are left alone.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 1. ffmpeg / ffprobe (media tests, e2e-dry)
if ! command -v ffprobe >/dev/null 2>&1; then
  apt-get update -qq >/dev/null 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends ffmpeg >/dev/null
fi

# 2. Python dependencies (uv keeps its cache in the container image)
uv sync --group dev --quiet

# 3. Local Postgres 16 for integration tests (tests are skipped when STUDIO_TEST_PG_URL is unset)
PGBIN=/usr/lib/postgresql/16/bin
PGDATA=/tmp/pgdata
if [ -x "$PGBIN/pg_ctl" ] && id postgres >/dev/null 2>&1; then
  if [ ! -s "$PGDATA/PG_VERSION" ]; then
    mkdir -p "$PGDATA" /tmp/pglog && chown postgres:postgres "$PGDATA" /tmp/pglog
    su postgres -c "$PGBIN/initdb -D $PGDATA -A trust -U postgres >/tmp/pglog/initdb.log 2>&1"
  fi
  if ! su postgres -c "$PGBIN/pg_ctl -D $PGDATA status" >/dev/null 2>&1; then
    su postgres -c "$PGBIN/pg_ctl -D $PGDATA -l /tmp/pglog/pg.log -o '-p 5432 -k /tmp -c listen_addresses=localhost' -w start" >/dev/null
  fi
  psql -h localhost -U postgres -tc "select 1 from pg_database where datname='studio_test'" | grep -q 1 \
    || psql -h localhost -U postgres -qc "create database studio_test" >/dev/null
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo 'export STUDIO_TEST_PG_URL="postgresql+psycopg://postgres@localhost:5432/studio_test"' >> "$CLAUDE_ENV_FILE"
  fi
fi
