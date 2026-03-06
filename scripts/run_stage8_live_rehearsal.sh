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
REPORT_FILE="$REPORT_DIR/stage8-live-rehearsal-${TS}.md"
RESULT_JSON="/tmp/stage8_live_rehearsal_${TS}.json"

LIVE_ENABLED="${NEWCLAW_STAGE8_LIVE_ENABLED:-0}"
MCP_ENDPOINT="${NEWCLAW_REDMINE_MCP_ENDPOINT:-}"
SANDBOX_BASE_URL="${NEWCLAW_STAGE8_SANDBOX_BASE_URL:-}"
SANDBOX_PROJECT="${NEWCLAW_STAGE8_SANDBOX_PROJECT:-}"
SANDBOX_ASSIGNEE="${NEWCLAW_STAGE8_SANDBOX_ASSIGNEE:-ops_oncall}"
SANDBOX_TRANSITION="${NEWCLAW_STAGE8_SANDBOX_TRANSITION:-In Progress}"
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

{
  echo "# Stage 8 Live Rehearsal Report"
  echo ""
  echo "- executed_at_utc: ${TS}"
  echo "- execution_mode: mcp-live"
  echo "- sandbox_enabled: ${LIVE_ENABLED}"
  echo "- sandbox_base_url: ${SANDBOX_BASE_URL:-not_configured}"
  echo "- sandbox_project: ${SANDBOX_PROJECT:-not_configured}"
  echo "- mcp_endpoint: ${MCP_ENDPOINT:-not_configured}"
  echo "- status: RUNNING"
  echo ""
  echo "## Checks"
} >"$REPORT_FILE"

if ! python3 -c 'import fastapi, httpx' >/tmp/stage8_live_rehearsal.out 2>/tmp/stage8_live_rehearsal.err; then
  STATUS="SKIP"
  SKIP_REASON="python runtime dependencies unavailable"
  log_line "- [SKIP] runtime dependencies"
  log_line "  - reason: ${SKIP_REASON}"
fi

if [[ "${STATUS}" == "PASS" ]] && ! is_truthy "${LIVE_ENABLED}"; then
  STATUS="SKIP"
  SKIP_REASON="NEWCLAW_STAGE8_LIVE_ENABLED is not enabled"
  log_line "- [SKIP] live enable flag"
  log_line "  - reason: ${SKIP_REASON}"
fi

if [[ "${STATUS}" == "PASS" ]] && [[ -z "${MCP_ENDPOINT}" || -z "${SANDBOX_BASE_URL}" || -z "${SANDBOX_PROJECT}" ]]; then
  STATUS="SKIP"
  SKIP_REASON="live sandbox target metadata is incomplete"
  log_line "- [SKIP] live sandbox metadata"
  log_line "  - reason: ${SKIP_REASON}"
fi

if [[ "${STATUS}" == "PASS" ]]; then
  if python3 scripts/stage8_live_rehearsal_runner.py >"${RESULT_JSON}" 2>/tmp/stage8_live_rehearsal.err; then
    pass "incident create flow executed in mcp-live mode"
    pass "redmine lifecycle actions executed (update/comment/assign/transition)"
    {
      echo ""
      echo "## Evidence"
      python3 - "$RESULT_JSON" "$SANDBOX_ASSIGNEE" "$SANDBOX_TRANSITION" <<'PY'
import json
import sys
from pathlib import Path

result_path = Path(sys.argv[1])
assignee = sys.argv[2]
transition = sys.argv[3]
payload = json.loads(result_path.read_text(encoding="utf-8"))
print(f"- task_id: {payload['task_id']}")
print(f"- incident_id: {payload['incident_id']}")
print(f"- issue_ref: {payload['issue_ref']}")
print(f"- run_mode: {payload['run_mode']}")
print(f"- report_path: {payload['report_path']}")
print(f"- event_count: {payload['event_count']}")
print(f"- requested_assignee: {assignee}")
print(f"- requested_transition: {transition}")
print("")
print("## Lifecycle Results")
for item in payload["lifecycle_results"]:
    print(f"- {item['method']}: status={item.get('status')} external_ref={item.get('external_ref') or item.get('issue_id')}")
PY
    } | tee -a "$REPORT_FILE"
  else
    fail "incident live rehearsal runner"
    log_line "  - stderr: $(tr '\n' ' ' </tmp/stage8_live_rehearsal.err)"
  fi
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

echo "Stage 8 live rehearsal completed."
