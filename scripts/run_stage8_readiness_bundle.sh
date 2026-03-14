#!/usr/bin/env bash
set -euo pipefail

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_DIR="reports/qa"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/stage8-readiness-bundle-${TS}.md"

STATUS="PASS"

required_envs=(
  "NEWCLAW_STAGE8_SANDBOX_ENABLED"
  "NEWCLAW_STAGE8_SANDBOX_BASE_URL"
  "NEWCLAW_STAGE8_SANDBOX_PROJECT"
  "NEWCLAW_STAGE8_LIVE_ENABLED"
  "NEWCLAW_REDMINE_MCP_ENDPOINT"
)

latest_report() {
  local pattern="$1"
  local result
  result="$(ls -t ${pattern} 2>/dev/null | head -n 1 || true)"
  printf "%s" "$result"
}

write_line() {
  echo "$1" | tee -a "$REPORT_FILE"
}

record_env() {
  local name="$1"
  local value="${!name:-}"
  if [[ -n "$value" ]]; then
    write_line "- [CONFIGURED] ${name}"
  else
    write_line "- [MISSING] ${name}"
    if [[ "$STATUS" == "PASS" ]]; then
      STATUS="BLOCKED"
    fi
  fi
}

run_step() {
  local label="$1"
  local pattern="$2"
  shift 2
  local code=0
  if "$@" >/tmp/stage8_readiness_bundle.out 2>/tmp/stage8_readiness_bundle.err; then
    write_line "- [PASS] ${label}"
  else
    code=$?
    if [[ "$code" -eq 10 ]]; then
      write_line "- [BLOCKED] ${label}"
      write_line "  - reason: $(tr '\n' ' ' </tmp/stage8_readiness_bundle.err)"
      if [[ "$STATUS" == "PASS" ]]; then
        STATUS="BLOCKED"
      fi
    else
      write_line "- [FAIL] ${label}"
      write_line "  - reason: $(tr '\n' ' ' </tmp/stage8_readiness_bundle.err)"
      STATUS="FAIL"
    fi
  fi
  local report_path
  report_path="$(latest_report "$pattern")"
  if [[ -n "$report_path" ]]; then
    write_line "  - report: ${report_path}"
  fi
}

{
  echo "# Stage 8 Readiness Bundle Report"
  echo ""
  echo "- executed_at_utc: ${TS}"
  echo "- status: RUNNING"
  echo ""
  echo "## Environment Checklist"
} >"$REPORT_FILE"

for name in "${required_envs[@]}"; do
  record_env "$name"
done

write_line ""
write_line "## Executions"
run_step "grouped self evaluation" "reports/qa/stage8-self-eval-*.md" bash scripts/run_stage8_self_eval.sh
run_step "sandbox rehearsal" "reports/qa/stage8-sandbox-e2e-*.md" bash scripts/run_stage8_sandbox_e2e.sh
run_step "live rehearsal" "reports/qa/stage8-live-rehearsal-*.md" bash scripts/run_stage8_live_rehearsal.sh

write_line ""
write_line "## Summary"
write_line "- status: ${STATUS}"
write_line "- report: ${REPORT_FILE}"

if [[ "$STATUS" == "FAIL" ]]; then
  exit 1
fi
if [[ "$STATUS" == "BLOCKED" ]]; then
  exit 20
fi
