#!/usr/bin/env bash
set -u -o pipefail

PASS_EXIT_CODE=0
FAIL_EXIT_CODE=1
SKIP_EXIT_CODE=10

TIMESTAMP_UTC="$(date -u +"%Y%m%dT%H%M%SZ")"
BASE_URL="${NEWCLAW_BROWSER_SMOKE_BASE_URL:-http://127.0.0.1:18080}"
AUTOSTART="${NEWCLAW_BROWSER_SMOKE_AUTOSTART:-1}"
SESSION_NAME="${NEWCLAW_BROWSER_SMOKE_SESSION:-newclaw-browser-smoke}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
PWCLI="${CODEX_HOME_DIR}/skills/playwright/scripts/playwright_cli.sh"
ARTIFACT_DIR="output/playwright/${TIMESTAMP_UTC}"

SERVER_STARTED=0
SERVER_PID=""
SERVER_LOG="/tmp/newclaw_browser_smoke_${TIMESTAMP_UTC}.log"

log() {
  echo "[browser-smoke] $*"
}

skip() {
  echo "[browser-smoke][SKIP] $*" >&2
  exit "${SKIP_EXIT_CODE}"
}

capture_failure_artifacts() {
  local reason="$1"

  mkdir -p "${ARTIFACT_DIR}"
  {
    echo "timestamp_utc=${TIMESTAMP_UTC}"
    echo "base_url=${BASE_URL}"
    echo "reason=${reason}"
    echo "session=${SESSION_NAME}"
  } >"${ARTIFACT_DIR}/failure.txt"

  (
    cd "${ARTIFACT_DIR}" || exit 0
    pw screenshot >screenshot.log 2>&1 || true
    pw console warning >console.log 2>&1 || pw console >console.log 2>&1 || true
    pw network >network.log 2>&1 || true
  )
}

fail() {
  local reason="$1"
  echo "[browser-smoke][FAIL] ${reason}" >&2
  capture_failure_artifacts "${reason}"
  exit "${FAIL_EXIT_CODE}"
}

pass() {
  log "$*"
  exit "${PASS_EXIT_CODE}"
}

cleanup() {
  if [[ "${SERVER_STARTED}" -eq 1 && -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

is_truthy() {
  local value
  value="$(printf "%s" "$1" | tr '[:upper:]' '[:lower:]')"
  [[ "${value}" == "1" || "${value}" == "true" || "${value}" == "yes" || "${value}" == "on" ]]
}

is_server_up() {
  curl -fsS --max-time 2 "${BASE_URL}/health" >/dev/null 2>&1
}

pw() {
  PLAYWRIGHT_CLI_SESSION="${SESSION_NAME}" "${PWCLI}" --session "${SESSION_NAME}" "$@"
}

if ! command -v npx >/dev/null 2>&1; then
  skip "npx not found on PATH"
fi

if [[ ! -x "${PWCLI}" ]]; then
  skip "playwright wrapper not executable: ${PWCLI}"
fi

if ! command -v python3 >/dev/null 2>&1; then
  skip "python3 not found on PATH"
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import fastapi  # noqa: F401
import uvicorn  # noqa: F401
PY
then
  skip "python runtime dependencies unavailable (fastapi/uvicorn)"
fi

if ! command -v curl >/dev/null 2>&1; then
  skip "curl not found on PATH"
fi

if ! is_server_up; then
  if ! is_truthy "${AUTOSTART}"; then
    fail "server unavailable and NEWCLAW_BROWSER_SMOKE_AUTOSTART is disabled"
  fi

  base_no_scheme="${BASE_URL#http://}"
  base_no_scheme="${base_no_scheme#https://}"
  host_port="${base_no_scheme%%/*}"
  server_host="${host_port%%:*}"
  server_port="${host_port##*:}"

  if [[ "${host_port}" == "${server_host}" ]]; then
    if [[ "${BASE_URL}" == https://* ]]; then
      server_port="443"
    else
      server_port="80"
    fi
  fi

  log "server not reachable, starting uvicorn at ${server_host}:${server_port}"
  uvicorn app.main:APP --host "${server_host}" --port "${server_port}" >"${SERVER_LOG}" 2>&1 &
  SERVER_PID="$!"
  SERVER_STARTED=1

  for _ in $(seq 1 60); do
    if is_server_up; then
      break
    fi
    if ! kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done

  if ! is_server_up; then
    fail "failed to start local server; see ${SERVER_LOG}"
  fi
fi

if ! pw open "${BASE_URL}/docs" >/tmp/newclaw_browser_smoke.out 2>/tmp/newclaw_browser_smoke.err; then
  fail "failed to open /docs: $(tr '\n' ' ' </tmp/newclaw_browser_smoke.err)"
fi

title="$(pw eval "document.title" 2>/tmp/newclaw_browser_smoke.err || true)"
title="$(printf "%s" "${title}" | tr -d '\r')"
if [[ "${title}" != *"Swagger UI"* ]]; then
  fail "unexpected docs title: ${title}"
fi

if ! pw open "${BASE_URL}/openapi.json" >/tmp/newclaw_browser_smoke.out 2>/tmp/newclaw_browser_smoke.err; then
  fail "failed to open /openapi.json: $(tr '\n' ' ' </tmp/newclaw_browser_smoke.err)"
fi

openapi_text="$(pw eval "document.body ? document.body.innerText : ''" 2>/tmp/newclaw_browser_smoke.err || true)"
for route in \
  "/api/v1/task/create" \
  "/api/v1/task/run" \
  "/api/v1/task/status/{task_id}"
do
  if ! printf "%s" "${openapi_text}" | rg -Fq "${route}"; then
    fail "required path missing in openapi: ${route}"
  fi
done

pass "swagger/openapi browser smoke passed"
