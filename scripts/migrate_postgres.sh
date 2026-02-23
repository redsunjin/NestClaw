#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-up}"
DATABASE_URL="${NEWCLAW_DATABASE_URL:-${2:-}}"

if [[ -z "$DATABASE_URL" ]]; then
  echo "NEWCLAW_DATABASE_URL is required (or pass as 2nd arg)."
  exit 2
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql command not found. Install PostgreSQL client first."
  exit 2
fi

case "$ACTION" in
  up)
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/postgres/001_init.sql
    ;;
  down)
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/postgres/001_down.sql
    ;;
  *)
    echo "Usage: $0 [up|down] [database_url]"
    exit 2
    ;;
esac

echo "Postgres migration '$ACTION' completed."
