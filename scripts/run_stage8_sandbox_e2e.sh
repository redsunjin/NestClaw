#!/usr/bin/env bash
set -euo pipefail

is_truthy() {
  local value
  value="$(printf "%s" "$1" | tr '[:upper:]' '[:lower:]')"
  [[ "${value}" == "1" || "${value}" == "true" || "${value}" == "yes" || "${value}" == "on" ]]
}

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_DIR="reports/qa"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/stage8-sandbox-e2e-${TS}.md"

SANDBOX_ENABLED="${NEWCLAW_STAGE8_SANDBOX_ENABLED:-0}"
SANDBOX_BASE_URL="${NEWCLAW_STAGE8_SANDBOX_BASE_URL:-}"
SANDBOX_PROJECT="${NEWCLAW_STAGE8_SANDBOX_PROJECT:-}"
STATUS="PASS"
SKIP_REASON=""
PASS_COUNT=0
FAIL_COUNT=0

log_line() {
  echo "$1" | tee -a "$REPORT_FILE"
}

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  log_line "- [PASS] $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  STATUS="FAIL"
  log_line "- [FAIL] $1"
}

run_check() {
  local label="$1"
  shift
  if "$@" >/tmp/stage8_sandbox.out 2>/tmp/stage8_sandbox.err; then
    pass "$label"
  else
    fail "$label"
    log_line "  - stderr: $(tr '\n' ' ' </tmp/stage8_sandbox.err)"
  fi
}

{
  echo "# Stage 8 Sandbox Rehearsal Report"
  echo ""
  echo "- executed_at_utc: ${TS}"
  echo "- execution_mode: rehearsal-dry-run"
  echo "- sandbox_enabled: ${SANDBOX_ENABLED}"
  echo "- sandbox_base_url: ${SANDBOX_BASE_URL:-not_configured}"
  echo "- sandbox_project: ${SANDBOX_PROJECT:-not_configured}"
  echo "- status: RUNNING"
  echo ""
  echo "## Checks"
} >"$REPORT_FILE"

if ! python3 -c 'import fastapi, httpx' >/tmp/stage8_sandbox.out 2>/tmp/stage8_sandbox.err; then
  STATUS="SKIP"
  SKIP_REASON="python runtime dependencies unavailable"
  log_line "- [SKIP] runtime dependencies"
  log_line "  - reason: ${SKIP_REASON}"
fi

if [[ "${STATUS}" == "PASS" ]] && ! is_truthy "${SANDBOX_ENABLED}"; then
  STATUS="SKIP"
  SKIP_REASON="NEWCLAW_STAGE8_SANDBOX_ENABLED is not enabled"
  log_line "- [SKIP] sandbox enable flag"
  log_line "  - reason: ${SKIP_REASON}"
fi

if [[ "${STATUS}" == "PASS" ]] && [[ -z "${SANDBOX_BASE_URL}" || -z "${SANDBOX_PROJECT}" ]]; then
  STATUS="SKIP"
  SKIP_REASON="sandbox target metadata is incomplete"
  log_line "- [SKIP] sandbox target metadata"
  log_line "  - reason: ${SKIP_REASON}"
fi

if [[ "${STATUS}" == "PASS" ]]; then
  run_check "incident runtime smoke tests" python3 -m unittest tests.test_incident_runtime_smoke
  run_check "incident policy gate tests" python3 -m unittest tests.test_incident_policy_gate
fi

{
  echo ""
  echo "## Summary"
  echo "- status: ${STATUS}"
  echo "- pass: ${PASS_COUNT}"
  echo "- fail: ${FAIL_COUNT}"
  if [[ -n "${SKIP_REASON}" ]]; then
    echo "- skip_reason: ${SKIP_REASON}"
  fi
  echo "- report: ${REPORT_FILE}"
} | tee -a "$REPORT_FILE"

if [[ "${STATUS}" == "SKIP" ]]; then
  exit 10
fi

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

echo "Stage 8 sandbox rehearsal completed."
