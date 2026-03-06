#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT="work/micro_units"
TEMPLATE_PATH="templates/MICRO_WORK_UNIT_TEMPLATE.md"

usage() {
  cat <<EOF
Usage:
  $0 init <unit-id> "<goal>" [target-stage]
  $0 gate-plan <unit-id>
  $0 gate-review <unit-id>
  $0 gate-implement <unit-id>
  $0 gate-evaluate <unit-id> [target-stage]
  $0 run <unit-id> [target-stage]
  $0 status <unit-id>
EOF
}

ts_now() {
  date -u +"%Y%m%dT%H%M%SZ"
}

unit_dir() {
  local unit_id="$1"
  printf "%s/%s" "$WORK_ROOT" "$unit_id"
}

require_unit_dir() {
  local unit_id="$1"
  local dir
  dir="$(unit_dir "$unit_id")"
  if [[ ! -d "$dir" ]]; then
    echo "[ERROR] unit directory not found: $dir"
    exit 1
  fi
}

write_unit_card() {
  local unit_id="$1"
  local goal="$2"
  local target_stage="$3"
  local created_at
  created_at="$(ts_now)"
  local dir
  dir="$(unit_dir "$unit_id")"
  local card="$dir/WORK_UNIT.md"

  if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "[ERROR] template missing: $TEMPLATE_PATH"
    exit 1
  fi

  sed \
    -e "s/__UNIT_ID__/${unit_id}/g" \
    -e "s/__GOAL__/${goal//\//\\/}/g" \
    -e "s/__TARGET_STAGE__/${target_stage}/g" \
    -e "s/__CREATED_AT__/${created_at}/g" \
    "$TEMPLATE_PATH" >"$card"
}

init_unit() {
  local unit_id="$1"
  local goal="$2"
  local target_stage="${3:-8}"
  local dir
  dir="$(unit_dir "$unit_id")"

  mkdir -p "$dir/reports"
  if [[ -f "$dir/WORK_UNIT.md" ]]; then
    echo "[ERROR] unit already exists: $dir/WORK_UNIT.md"
    exit 1
  fi

  write_unit_card "$unit_id" "$goal" "$target_stage"

  cat >"$dir/PLAN_NOTES.md" <<EOF
# Plan Notes

## Scope
TODO

## Out of Scope
TODO

## Acceptance Criteria
TODO

## Risks
TODO

## Test Plan
TODO
EOF

  cat >"$dir/REVIEW_NOTES.md" <<EOF
# Review Notes

## Security / Policy Review
TODO

## Architecture / Workflow Review
TODO

## QA Gate Review
TODO

## Review Verdict
TODO
EOF

  cat >"$dir/IMPLEMENT_NOTES.md" <<EOF
# Implement Notes

## Changed Files
TODO

## Rollback Plan
TODO

## Known Risks
TODO
EOF

  cat >"$dir/EVALUATE_NOTES.md" <<EOF
# Evaluate Notes

## QA Result Summary
TODO

## Skip/Failure Reasons
TODO

## Next Action
TODO
EOF

  echo "[OK] micro unit initialized: $dir"
}

phase_report_open() {
  local unit_id="$1"
  local phase="$2"
  local ts
  ts="$(ts_now)"
  local report_path
  report_path="$(unit_dir "$unit_id")/reports/${phase}-${ts}.md"
  PHASE_REPORT="$report_path"
  PASS_COUNT=0
  FAIL_COUNT=0
  {
    echo "# Micro Phase Gate Report"
    echo ""
    echo "- unit_id: $unit_id"
    echo "- phase: $phase"
    echo "- executed_at_utc: $ts"
    echo ""
    echo "## Checks"
  } >"$PHASE_REPORT"
}

phase_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "- [PASS] $1" | tee -a "$PHASE_REPORT"
}

phase_fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "- [FAIL] $1" | tee -a "$PHASE_REPORT"
}

check_file_exists() {
  local file="$1"
  local label="$2"
  if [[ -f "$file" ]]; then
    phase_pass "$label"
  else
    phase_fail "$label"
  fi
}

check_pattern() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if rg -q "$pattern" "$file"; then
    phase_pass "$label"
  else
    phase_fail "$label"
  fi
}

check_no_todo() {
  local file="$1"
  local label="$2"
  if rg -qi "TODO|TBD" "$file"; then
    phase_fail "$label"
  else
    phase_pass "$label"
  fi
}

phase_report_close() {
  {
    echo ""
    echo "## Summary"
    echo "- pass: $PASS_COUNT"
    echo "- fail: $FAIL_COUNT"
    echo "- report: $PHASE_REPORT"
  } | tee -a "$PHASE_REPORT"

  if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo "[FAIL] phase gate failed: $PHASE_REPORT"
    exit 1
  fi
  echo "[OK] phase gate passed: $PHASE_REPORT"
}

gate_plan() {
  local unit_id="$1"
  require_unit_dir "$unit_id"
  local dir
  dir="$(unit_dir "$unit_id")"
  local file="$dir/PLAN_NOTES.md"

  phase_report_open "$unit_id" "plan-gate"
  check_file_exists "$file" "plan notes exists"
  if [[ -f "$file" ]]; then
    check_pattern "$file" "^## Scope" "contains scope section"
    check_pattern "$file" "^## Out of Scope" "contains out of scope section"
    check_pattern "$file" "^## Acceptance Criteria" "contains acceptance criteria section"
    check_pattern "$file" "^## Risks" "contains risk section"
    check_pattern "$file" "^## Test Plan" "contains test plan section"
    check_no_todo "$file" "plan notes resolved (no TODO/TBD)"
  fi
  phase_report_close
}

gate_review() {
  local unit_id="$1"
  require_unit_dir "$unit_id"
  local dir
  dir="$(unit_dir "$unit_id")"
  local file="$dir/REVIEW_NOTES.md"

  phase_report_open "$unit_id" "review-gate"
  check_file_exists "$file" "review notes exists"
  if [[ -f "$file" ]]; then
    check_pattern "$file" "^## Security / Policy Review" "contains security review"
    check_pattern "$file" "^## Architecture / Workflow Review" "contains architecture review"
    check_pattern "$file" "^## QA Gate Review" "contains qa gate review"
    check_pattern "$file" "^## Review Verdict" "contains review verdict"
    check_no_todo "$file" "review notes resolved (no TODO/TBD)"
  fi

  if python3 -m unittest tests.test_stage8_contract >/tmp/micro_review.out 2>/tmp/micro_review.err; then
    phase_pass "stage8 contract tests pass"
  else
    phase_fail "stage8 contract tests pass"
    echo "  - stderr: $(tr '\n' ' ' </tmp/micro_review.err)" | tee -a "$PHASE_REPORT"
  fi
  phase_report_close
}

gate_implement() {
  local unit_id="$1"
  require_unit_dir "$unit_id"
  local dir
  dir="$(unit_dir "$unit_id")"
  local file="$dir/IMPLEMENT_NOTES.md"

  phase_report_open "$unit_id" "implement-gate"
  check_file_exists "$file" "implement notes exists"
  if [[ -f "$file" ]]; then
    check_pattern "$file" "^## Changed Files" "contains changed files section"
    check_pattern "$file" "^## Rollback Plan" "contains rollback plan section"
    check_pattern "$file" "^## Known Risks" "contains known risk section"
    check_pattern "$file" '`.+`' "contains at least one changed file path"
    check_no_todo "$file" "implement notes resolved (no TODO/TBD)"
  fi
  phase_report_close
}

gate_evaluate() {
  local unit_id="$1"
  local target_stage="${2:-8}"
  require_unit_dir "$unit_id"
  local dir
  dir="$(unit_dir "$unit_id")"
  local file="$dir/EVALUATE_NOTES.md"

  phase_report_open "$unit_id" "evaluate-gate"
  check_file_exists "$file" "evaluate notes exists"
  if [[ -f "$file" ]]; then
    check_pattern "$file" "^## QA Result Summary" "contains qa result summary"
    check_pattern "$file" "^## Skip/Failure Reasons" "contains skip/failure reasons"
    check_pattern "$file" "^## Next Action" "contains next action section"
    check_no_todo "$file" "evaluate notes resolved (no TODO/TBD)"
  fi

  local cycle_output
  set +e
  if [[ "$target_stage" == "8" ]]; then
    cycle_output="$(env NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh "$target_stage" 2>&1)"
  else
    cycle_output="$(bash scripts/run_dev_qa_cycle.sh "$target_stage" 2>&1)"
  fi
  local rc=$?
  set -e
  local cycle_log="$dir/reports/evaluate-cycle-$(ts_now).log"
  printf "%s\n" "$cycle_output" >"$cycle_log"
  local cycle_report
  cycle_report="$(printf "%s\n" "$cycle_output" | sed -n 's/^- report: //p' | tail -n 1)"

  if [[ "$rc" -eq 0 ]]; then
    phase_pass "dev qa cycle stage ${target_stage} passed"
  else
    phase_fail "dev qa cycle stage ${target_stage} passed"
  fi
  if [[ -n "$cycle_report" ]]; then
    phase_pass "cycle report captured: $cycle_report"
  else
    phase_fail "cycle report captured"
  fi
  phase_pass "cycle raw log saved: $cycle_log"
  phase_report_close
}

run_all() {
  local unit_id="$1"
  local target_stage="${2:-8}"
  gate_plan "$unit_id"
  gate_review "$unit_id"
  gate_implement "$unit_id"
  gate_evaluate "$unit_id" "$target_stage"
}

status_unit() {
  local unit_id="$1"
  require_unit_dir "$unit_id"
  local dir
  dir="$(unit_dir "$unit_id")"
  echo "unit: $unit_id"
  echo "path: $dir"
  ls -1 "$dir"
  echo "--- latest reports ---"
  ls -1t "$dir/reports" 2>/dev/null | head -n 10 || true
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    init)
      [[ $# -ge 3 ]] || { usage; exit 2; }
      init_unit "$2" "$3" "${4:-8}"
      ;;
    gate-plan)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      gate_plan "$2"
      ;;
    gate-review)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      gate_review "$2"
      ;;
    gate-implement)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      gate_implement "$2"
      ;;
    gate-evaluate)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      gate_evaluate "$2" "${3:-8}"
      ;;
    run)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      run_all "$2" "${3:-8}"
      ;;
    status)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      status_unit "$2"
      ;;
    *)
      usage
      exit 2
      ;;
  esac
}

main "$@"
