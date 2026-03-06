#!/usr/bin/env bash
set -euo pipefail

STRICT="${NEWCLAW_STAGE8_SELF_EVAL_STRICT:-0}"
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_DIR="reports/qa"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/stage8-self-eval-${TS}.md"

PASS_COUNT=0
PENDING_COUNT=0
FAIL_COUNT=0
TOTAL_SCORE=0
MAX_SCORE=8

log_line() {
  echo "$1" | tee -a "$REPORT_FILE"
}

group_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  TOTAL_SCORE=$((TOTAL_SCORE + 2))
  log_line "- [PASS] $1"
}

group_pending() {
  PENDING_COUNT=$((PENDING_COUNT + 1))
  TOTAL_SCORE=$((TOTAL_SCORE + 1))
  log_line "- [PENDING] $1"
}

group_fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  log_line "- [FAIL] $1"
}

run_check() {
  local label="$1"
  shift
  if "$@" >/tmp/stage8_self_eval.out 2>/tmp/stage8_self_eval.err; then
    log_line "  - [PASS] ${label}"
    return 0
  fi
  log_line "  - [FAIL] ${label}"
  log_line "    - stderr: $(tr '\n' ' ' </tmp/stage8_self_eval.err)"
  return 1
}

run_check_allow_skip() {
  local label="$1"
  shift
  if "$@" >/tmp/stage8_self_eval.out 2>/tmp/stage8_self_eval.err; then
    if rg -q "skipped=[1-9]" /tmp/stage8_self_eval.out || rg -q "skipped=[1-9]" /tmp/stage8_self_eval.err; then
      log_line "  - [PENDING] ${label}"
      log_line "    - reason: command reported skipped tests"
      return 2
    fi
    log_line "  - [PASS] ${label}"
    return 0
  fi
  log_line "  - [FAIL] ${label}"
  log_line "    - stderr: $(tr '\n' ' ' </tmp/stage8_self_eval.err)"
  return 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]]
}

{
  echo "# Stage 8 Self-Evaluation Report"
  echo ""
  echo "- executed_at_utc: ${TS}"
  echo "- strict_mode: ${STRICT}"
  echo ""
  echo "## Group Results"
} >"$REPORT_FILE"

# G1: Adapter Contract Foundation
log_line "### G1 Adapter Contract Foundation"
g1_ok=1
run_check "adapter contract tests" python3 -m unittest tests.test_incident_adapter_contract || g1_ok=0
run_check "stage8 contract tests" python3 -m unittest tests.test_stage8_contract || g1_ok=0
if [[ -f "work/micro_units/stage8-w2-001/WORK_UNIT.md" ]]; then
  if rg -q -- '- status: `DONE`' work/micro_units/stage8-w2-001/WORK_UNIT.md; then
    log_line "  - [PASS] stage8-w2-001 is DONE"
  else
    log_line "  - [FAIL] stage8-w2-001 is DONE"
    g1_ok=0
  fi
else
  log_line "  - [FAIL] work unit missing: stage8-w2-001"
  g1_ok=0
fi

if [[ "$g1_ok" -eq 1 ]]; then
  group_pass "G1"
else
  group_fail "G1"
fi

# G2: Incident Orchestration Integration
log_line ""
log_line "### G2 Incident Orchestration Integration"
if require_file "tests/test_incident_runtime_smoke.py" && [[ -d "work/micro_units/stage8-w3-001" ]]; then
  g2_ok=1
  g2_pending=0
  set +e
  run_check_allow_skip "incident runtime smoke tests" python3 -m unittest tests.test_incident_runtime_smoke
  smoke_rc=$?
  set -e
  if [[ "$smoke_rc" -eq 1 ]]; then
    g2_ok=0
  elif [[ "$smoke_rc" -eq 2 ]]; then
    g2_pending=1
  fi
  run_check "stage8-w3-001 full micro cycle" bash scripts/run_micro_cycle.sh run stage8-w3-001 8 || g2_ok=0
  if [[ "$g2_ok" -eq 0 ]]; then
    group_fail "G2"
  elif [[ "$g2_pending" -eq 1 ]]; then
    group_pending "G2 (runtime smoke skipped)"
  else
    group_pass "G2"
  fi
else
  group_pending "G2 (missing tests/test_incident_runtime_smoke.py or stage8-w3-001)"
fi

# G3: Policy & Approval Classification
log_line ""
log_line "### G3 Policy & Approval Classification"
if require_file "tests/test_incident_policy_gate.py" && [[ -d "work/micro_units/stage8-w3-002" ]]; then
  g3_ok=1
  run_check "incident policy gate tests" python3 -m unittest tests.test_incident_policy_gate || g3_ok=0
  run_check "stage8-w3-002 full micro cycle" bash scripts/run_micro_cycle.sh run stage8-w3-002 8 || g3_ok=0
  if [[ "$g3_ok" -eq 1 ]]; then
    group_pass "G3"
  else
    group_fail "G3"
  fi
else
  group_pending "G3 (missing tests/test_incident_policy_gate.py or stage8-w3-002)"
fi

# G4: Quality Gate & Sandbox Readiness
log_line ""
log_line "### G4 Quality Gate & Sandbox Readiness"
sandbox_report_count="$(find reports/qa -maxdepth 1 -type f -name 'stage8-sandbox-e2e-*.md' | wc -l | tr -d ' ')"
if rg -q "tests.test_incident_adapter_contract|run_dev_qa_cycle.sh 8" .github/workflows/quality-gate.yml && [[ "$sandbox_report_count" -gt 0 ]]; then
  g4_ok=1
  run_check "next stage pipeline stage8" bash scripts/run_next_stage_pipeline.sh 8 2 1 NEXT_STAGE_PLAN_2026-02-24.md || g4_ok=0
  if [[ "$g4_ok" -eq 1 ]]; then
    group_pass "G4"
  else
    group_fail "G4"
  fi
else
  group_pending "G4 (missing Stage8 CI wiring or stage8-sandbox-e2e report)"
fi

READY_PCT=$((TOTAL_SCORE * 100 / MAX_SCORE))

{
  echo ""
  echo "## Summary"
  echo "- pass_groups: ${PASS_COUNT}"
  echo "- pending_groups: ${PENDING_COUNT}"
  echo "- fail_groups: ${FAIL_COUNT}"
  echo "- readiness_score: ${TOTAL_SCORE}/${MAX_SCORE} (${READY_PCT}%)"
  echo "- report: ${REPORT_FILE}"
} | tee -a "$REPORT_FILE"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  echo "Stage 8 self-evaluation failed."
  exit 1
fi

if [[ "$STRICT" == "1" && "$PENDING_COUNT" -gt 0 ]]; then
  echo "Stage 8 self-evaluation strict mode failed due to pending groups."
  exit 1
fi

echo "Stage 8 self-evaluation completed."
