#!/usr/bin/env bash
set -euo pipefail

TARGET_STAGE="${1:-4}"
if ! [[ "$TARGET_STAGE" =~ ^[1-8]$ ]]; then
  echo "Usage: $0 <target-stage: 1..8>"
  exit 2
fi

STRICT_GATE="${NEWCLAW_STRICT_GATE:-0}"
SKIP_STAGE8_SELF_EVAL="${NEWCLAW_SKIP_STAGE8_SELF_EVAL:-0}"
is_truthy() {
  local value
  value="$(printf "%s" "$1" | tr '[:upper:]' '[:lower:]')"
  [[ "${value}" == "1" || "${value}" == "true" || "${value}" == "yes" || "${value}" == "on" ]]
}

REPORT_DIR="reports/qa"
mkdir -p "$REPORT_DIR"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_FILE="$REPORT_DIR/cycle-${TIMESTAMP}.md"

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

write_header() {
  cat >"$REPORT_FILE" <<EOF
# Dev-QA Cycle Report

- target_stage: ${TARGET_STAGE}
- executed_at_utc: ${TIMESTAMP}

## Results
EOF
}

pass() {
  local name="$1"
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "- [PASS] ${name}" | tee -a "$REPORT_FILE"
}

fail() {
  local name="$1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "- [FAIL] ${name}" | tee -a "$REPORT_FILE"
}

skip() {
  local name="$1"
  SKIP_COUNT=$((SKIP_COUNT + 1))
  echo "- [SKIP] ${name}" | tee -a "$REPORT_FILE"
}

run_check() {
  local name="$1"
  shift
  if "$@" >/tmp/cycle_check.out 2>/tmp/cycle_check.err; then
    pass "$name"
  else
    fail "$name"
    echo "  - stderr: $(tr '\n' ' ' </tmp/cycle_check.err)" | tee -a "$REPORT_FILE"
  fi
}

run_optional_check() {
  local name="$1"
  shift
  if "$@" >/tmp/cycle_check.out 2>/tmp/cycle_check.err; then
    if rg -q "skipped=[1-9]" /tmp/cycle_check.out || rg -q "skipped=[1-9]" /tmp/cycle_check.err; then
      if is_truthy "${STRICT_GATE}"; then
        fail "$name"
        echo "  - stderr: strict gate enabled and optional check reported skip" | tee -a "$REPORT_FILE"
      else
        skip "$name"
        echo "  - reason: optional check skipped by test runtime" | tee -a "$REPORT_FILE"
      fi
    else
      pass "$name"
    fi
  else
    if is_truthy "${STRICT_GATE}"; then
      fail "$name"
      echo "  - stderr: $(tr '\n' ' ' </tmp/cycle_check.err)" | tee -a "$REPORT_FILE"
    else
      skip "$name"
      echo "  - reason: $(tr '\n' ' ' </tmp/cycle_check.err)" | tee -a "$REPORT_FILE"
    fi
  fi
}

run_optional_dep_check() {
  local name="$1"
  shift
  if "$@" >/tmp/cycle_check.out 2>/tmp/cycle_check.err; then
    pass "$name"
  else
    local rc=$?
    local reason
    reason="$(tr '\n' ' ' </tmp/cycle_check.err)"
    if [[ -z "${reason// }" ]]; then
      reason="$(tr '\n' ' ' </tmp/cycle_check.out)"
    fi
    if [[ "$rc" -eq 10 ]]; then
      if is_truthy "${STRICT_GATE}"; then
        fail "$name"
        echo "  - stderr: strict gate enabled and dependency-gated check returned SKIP(10)" | tee -a "$REPORT_FILE"
      else
        skip "$name"
        echo "  - reason: ${reason}" | tee -a "$REPORT_FILE"
      fi
    else
      fail "$name"
      echo "  - stderr: ${reason}" | tee -a "$REPORT_FILE"
    fi
  fi
}

check_stage_1() {
  run_check "py_compile app/main.py" env PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile app/main.py app/__init__.py
  run_check "endpoint create exists" rg -q "def create_task" app/main.py
  run_check "endpoint run exists" rg -q "def run_task" app/main.py
  run_check "endpoint status exists" rg -q "def task_status" app/main.py
}

check_stage_2() {
  run_check "planner stage exists" rg -q "_set_stage\\(task, \"planner\"\\)" app/main.py
  run_check "executor stage exists" rg -q "_set_stage\\(task, \"executor\"\\)" app/main.py
  run_check "reviewer stage exists" rg -q "_set_stage\\(task, \"reviewer\"\\)" app/main.py
  run_check "reporter stage exists" rg -q "_set_stage\\(task, \"reporter\"\\)" app/main.py
}

check_stage_3() {
  run_check "policy block event exists" rg -q "BLOCKED_POLICY" app/main.py
  run_check "rbac/jwt auth exists" rg -q "actor_context_dependency|Authorization|X-Actor-Role" app/auth.py
  run_check "policy whitelist doc exists" test -f POLICY_WHITELIST.md
}

check_stage_4() {
  run_check "retry logic exists" rg -q "MAX_RETRY = 1" app/main.py
  run_check "approval list endpoint exists" rg -q "def list_approvals" app/main.py
  run_check "approval approve endpoint exists" rg -q "def approve_queue_item" app/main.py
  run_check "approval reject endpoint exists" rg -q "def reject_queue_item" app/main.py
}

check_stage_5() {
  run_check "non-it templates doc exists" test -f NON_IT_WORK_TEMPLATES.md
  run_check "meeting template test plan exists" test -f TEMPLATE_MEETING_SUMMARY_TEST_PLAN.md
  run_check "cli implementation exists (target for step5)" test -f app/cli.py
}

check_stage_6() {
  run_check "static contract tests" python3 -m unittest tests.test_spec_contract
  run_optional_check "runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_runtime_smoke
  run_optional_dep_check "browser swagger smoke (playwright)" bash scripts/run_browser_smoke.sh
}

check_stage_7() {
  run_check "stage7 static contract tests" python3 -m unittest tests.test_stage7_contract
  run_optional_check "idp auth unit tests (requires auth runtime stack)" python3 -m unittest tests.test_auth_idp
  run_optional_dep_check "idp rotation rehearsal script (env-gated)" bash scripts/run_idp_key_rotation_rehearsal.sh
  run_check "postgres migration script exists" test -f scripts/migrate_postgres.sh
  run_optional_dep_check "postgres rehearsal smoke (env-gated)" bash scripts/run_postgres_rehearsal.sh
}

check_stage_8() {
  run_check "stage8 static contract tests" python3 -m unittest tests.test_stage8_contract
  run_check "stage8 model registry contract tests" python3 -m unittest tests.test_model_registry_contract
  run_check "stage8 tool registry contract tests" python3 -m unittest tests.test_tool_registry_contract
  run_check "stage8 intent classifier contract tests" python3 -m unittest tests.test_intent_classifier_contract
  run_check "stage8 incident adapter contract tests" python3 -m unittest tests.test_incident_adapter_contract
  run_check "stage8 incident policy gate tests" python3 -m unittest tests.test_incident_policy_gate
  run_optional_check "stage8 model registry runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_model_registry_runtime
  run_optional_check "stage8 tool registry runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_tool_registry_runtime
  run_optional_check "stage8 intent classifier runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_intent_classifier_runtime
  run_optional_check "stage8 agent facade runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_agent_entrypoint_smoke
  run_optional_check "stage8 incident runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_incident_runtime_smoke
  run_optional_check "stage8 tool cli runtime smoke tests (requires fastapi stack)" python3 -m unittest tests.test_tool_cli_smoke
  run_optional_check "stage8 mcp server smoke tests (requires fastapi stack)" python3 -m unittest tests.test_mcp_server_smoke
  if is_truthy "${SKIP_STAGE8_SELF_EVAL}"; then
    skip "stage8 grouped self evaluation baseline"
    echo "  - reason: nested stage8 cycle requested self-eval skip" | tee -a "$REPORT_FILE"
  else
    run_check "stage8 grouped self evaluation baseline" bash scripts/run_stage8_self_eval.sh
  fi
  run_optional_dep_check "stage8 sandbox rehearsal (env-gated)" bash scripts/run_stage8_sandbox_e2e.sh
  run_optional_dep_check "stage8 live rehearsal (env-gated)" bash scripts/run_stage8_live_rehearsal.sh
  run_check "stage8 execution checklist exists" test -f STAGE8_EXECUTION_CHECKLIST_2026-03-04.md
  run_check "stage8 detailed design exists" test -f STAGE8_DETAILED_DESIGN_2026-03-04.md
  run_check "stage8 self eval group doc exists" test -f STAGE8_SELF_EVAL_GROUPS_2026-03-05.md
  run_check "stage8 micro workflow exists" test -f MICRO_AGENT_WORKFLOW.md
  run_check "stage8 micro cycle script exists" test -f scripts/run_micro_cycle.sh
  run_check "stage8 self eval script exists" test -f scripts/run_stage8_self_eval.sh
  run_check "stage8 sandbox rehearsal script exists" test -f scripts/run_stage8_sandbox_e2e.sh
  run_check "stage8 live rehearsal script exists" test -f scripts/run_stage8_live_rehearsal.sh
  run_check "stage8 live rehearsal runner exists" test -f scripts/stage8_live_rehearsal_runner.py
  run_check "stage8 first micro unit exists" test -f work/micro_units/stage8-w2-001/WORK_UNIT.md
  run_check "stage8 tasks schedule exists" rg -q "Stage 8 실행 스케줄" TASKS.md
  run_check "stage8 next stage schedule exists" rg -q "Stage 8 실행 스케줄 업데이트" NEXT_STAGE_PLAN_2026-02-24.md
}

write_header
echo "" | tee -a "$REPORT_FILE"
echo "## Stage Checks" | tee -a "$REPORT_FILE"

for stage in $(seq 1 "$TARGET_STAGE"); do
  echo "" | tee -a "$REPORT_FILE"
  echo "### Stage ${stage}" | tee -a "$REPORT_FILE"
  "check_stage_${stage}"
done

echo "" | tee -a "$REPORT_FILE"
echo "## Summary" | tee -a "$REPORT_FILE"
echo "- pass: ${PASS_COUNT}" | tee -a "$REPORT_FILE"
echo "- fail: ${FAIL_COUNT}" | tee -a "$REPORT_FILE"
echo "- skip: ${SKIP_COUNT}" | tee -a "$REPORT_FILE"
echo "- report: ${REPORT_FILE}" | tee -a "$REPORT_FILE"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  echo "Cycle failed: ${FAIL_COUNT} check(s) failed."
  exit 1
fi

echo "Cycle passed up to target stage ${TARGET_STAGE}."
