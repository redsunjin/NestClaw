#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"

ROOT_DIR="${NEWCLAW_LOCAL_PG_ROOT:-$PWD/.local}"
PG_BIN_DIR="${NEWCLAW_LOCAL_PG_BIN:-${ROOT_DIR}/pgsql/bin}"
PG_DATA_DIR="${NEWCLAW_LOCAL_PGDATA:-${ROOT_DIR}/pgdata}"
PG_LOG_FILE="${NEWCLAW_LOCAL_PG_LOG:-${ROOT_DIR}/postgres.log}"
PG_HOST="${NEWCLAW_LOCAL_PG_HOST:-127.0.0.1}"
PG_PORT="${NEWCLAW_LOCAL_PG_PORT:-55432}"
PG_DB="${NEWCLAW_LOCAL_PG_DB:-new_claw}"
INIT_IF_MISSING="${NEWCLAW_LOCAL_PG_INIT_IF_MISSING:-0}"

PG_CTL="${PG_BIN_DIR}/pg_ctl"
INITDB="${PG_BIN_DIR}/initdb"
CREATEDB="${PG_BIN_DIR}/createdb"
PG_ISREADY="${PG_BIN_DIR}/pg_isready"

usage() {
  cat <<EOF
Usage:
  $0 [status|start|stop|restart|dsn]

Behavior:
  - Operates only on workspace-local PostgreSQL cluster.
  - Does not touch system/global PostgreSQL instances.

Environment overrides:
  NEWCLAW_LOCAL_PG_ROOT
  NEWCLAW_LOCAL_PG_BIN
  NEWCLAW_LOCAL_PGDATA
  NEWCLAW_LOCAL_PG_LOG
  NEWCLAW_LOCAL_PG_HOST
  NEWCLAW_LOCAL_PG_PORT
  NEWCLAW_LOCAL_PG_DB
  NEWCLAW_LOCAL_PG_INIT_IF_MISSING=1   # initialize cluster on start if absent
EOF
}

require_pg_ctl() {
  if [[ ! -x "${PG_CTL}" ]]; then
    echo "[local-postgres][FAIL] pg_ctl not found: ${PG_CTL}" >&2
    echo "hint: build/install local postgres under ${ROOT_DIR}/pgsql or set NEWCLAW_LOCAL_PG_BIN" >&2
    exit 2
  fi
}

ensure_cluster_exists() {
  if [[ -d "${PG_DATA_DIR}" ]]; then
    return 0
  fi
  if [[ "${INIT_IF_MISSING}" != "1" ]]; then
    echo "[local-postgres][FAIL] cluster not initialized: ${PG_DATA_DIR}" >&2
    echo "hint: set NEWCLAW_LOCAL_PG_INIT_IF_MISSING=1 and run start" >&2
    exit 2
  fi
  if [[ ! -x "${INITDB}" ]]; then
    echo "[local-postgres][FAIL] initdb not found: ${INITDB}" >&2
    exit 2
  fi
  mkdir -p "${ROOT_DIR}"
  "${INITDB}" -D "${PG_DATA_DIR}" -A trust >/tmp/newclaw_local_pg_init.out 2>/tmp/newclaw_local_pg_init.err || {
    echo "[local-postgres][FAIL] initdb failed: $(tr '\n' ' ' </tmp/newclaw_local_pg_init.err)" >&2
    exit 1
  }
  echo "[local-postgres] initialized cluster: ${PG_DATA_DIR}"
}

is_running() {
  "${PG_CTL}" -D "${PG_DATA_DIR}" status >/tmp/newclaw_local_pg_status.out 2>/tmp/newclaw_local_pg_status.err
}

start_pg() {
  require_pg_ctl
  ensure_cluster_exists

  if is_running; then
    echo "[local-postgres] already running"
    return 0
  fi

  mkdir -p "$(dirname "${PG_LOG_FILE}")"
  "${PG_CTL}" -D "${PG_DATA_DIR}" -l "${PG_LOG_FILE}" -o "-p ${PG_PORT} -h ${PG_HOST}" start \
    >/tmp/newclaw_local_pg_start.out 2>/tmp/newclaw_local_pg_start.err || {
    echo "[local-postgres][FAIL] start failed: $(tr '\n' ' ' </tmp/newclaw_local_pg_start.err)" >&2
    exit 1
  }

  if [[ -x "${CREATEDB}" ]]; then
    "${CREATEDB}" -h "${PG_HOST}" -p "${PG_PORT}" "${PG_DB}" >/tmp/newclaw_local_pg_createdb.out 2>/tmp/newclaw_local_pg_createdb.err || true
  fi

  if [[ -x "${PG_ISREADY}" ]]; then
    "${PG_ISREADY}" -h "${PG_HOST}" -p "${PG_PORT}" >/tmp/newclaw_local_pg_isready.out 2>/tmp/newclaw_local_pg_isready.err || {
      echo "[local-postgres][FAIL] server started but readiness check failed: $(tr '\n' ' ' </tmp/newclaw_local_pg_isready.err)" >&2
      exit 1
    }
  fi

  echo "[local-postgres][PASS] started on ${PG_HOST}:${PG_PORT}"
}

stop_pg() {
  require_pg_ctl
  if [[ ! -d "${PG_DATA_DIR}" ]]; then
    echo "[local-postgres] cluster not initialized: ${PG_DATA_DIR}"
    return 0
  fi
  if ! is_running; then
    echo "[local-postgres] already stopped"
    return 0
  fi
  "${PG_CTL}" -D "${PG_DATA_DIR}" stop -m fast >/tmp/newclaw_local_pg_stop.out 2>/tmp/newclaw_local_pg_stop.err || {
    echo "[local-postgres][FAIL] stop failed: $(tr '\n' ' ' </tmp/newclaw_local_pg_stop.err)" >&2
    exit 1
  }
  echo "[local-postgres][PASS] stopped"
}

status_pg() {
  require_pg_ctl
  if [[ ! -d "${PG_DATA_DIR}" ]]; then
    echo "[local-postgres] cluster not initialized: ${PG_DATA_DIR}"
    exit 2
  fi
  if is_running; then
    cat /tmp/newclaw_local_pg_status.out
    exit 0
  fi
  cat /tmp/newclaw_local_pg_status.err >&2
  exit 1
}

print_dsn() {
  echo "postgresql://${USER}@${PG_HOST}:${PG_PORT}/${PG_DB}"
}

case "${ACTION}" in
  status)
    status_pg
    ;;
  start)
    start_pg
    ;;
  stop)
    stop_pg
    ;;
  restart)
    stop_pg
    start_pg
    ;;
  dsn)
    print_dsn
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "invalid action: ${ACTION}" >&2
    usage
    exit 2
    ;;
esac
