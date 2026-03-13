#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MICRO_CYCLE="$SCRIPT_DIR/run_micro_cycle.sh"
WORK_ROOT="work/micro_units"

usage() {
  cat <<EOF
Usage:
  $0 prepare <unit-id> "<goal>" [target-stage]
  $0 status <unit-id> [target-stage]
  $0 verify <unit-id> [target-stage]
EOF
}

ts_now() {
  date -u +"%Y%m%dT%H%M%SZ"
}

unit_dir() {
  printf "%s/%s" "$WORK_ROOT" "$1"
}

require_unit() {
  local dir
  dir="$(unit_dir "$1")"
  if [[ ! -d "$dir" ]]; then
    echo "[ERROR] unit directory not found: $dir"
    exit 1
  fi
}

work_unit_file() {
  printf "%s/WORK_UNIT.md" "$(unit_dir "$1")"
}

phase_state() {
  local unit_id="$1"
  local label="$2"
  local file
  file="$(work_unit_file "$unit_id")"
  if rg -q --fixed-strings -- "- [x] ${label}" "$file"; then
    echo "done"
  else
    echo "pending"
  fi
}

next_owner() {
  local unit_id="$1"
  if [[ "$(phase_state "$unit_id" "Plan gate passed")" != "done" ]]; then
    echo "A01 Product Planner"
    return
  fi
  if [[ "$(phase_state "$unit_id" "Review gate passed")" != "done" ]]; then
    echo "A04 Security Reviewer"
    return
  fi
  if [[ "$(phase_state "$unit_id" "Implement gate passed")" != "done" ]]; then
    echo "A02 Workflow Engineer"
    return
  fi
  if [[ "$(phase_state "$unit_id" "Evaluate gate passed")" != "done" ]]; then
    echo "A06 QA Reliability"
    return
  fi
  echo "A09 Release Sync"
}

next_command() {
  local unit_id="$1"
  local stage="$2"
  if [[ "$(phase_state "$unit_id" "Plan gate passed")" != "done" ]]; then
    echo "Fill PLAN_NOTES.md, then: bash scripts/run_micro_cycle.sh gate-plan ${unit_id}"
    return
  fi
  if [[ "$(phase_state "$unit_id" "Review gate passed")" != "done" ]]; then
    echo "Fill REVIEW_NOTES.md, then: bash scripts/run_micro_cycle.sh gate-review ${unit_id}"
    return
  fi
  if [[ "$(phase_state "$unit_id" "Implement gate passed")" != "done" ]]; then
    echo "Implement changes and fill IMPLEMENT_NOTES.md, then: bash scripts/run_micro_cycle.sh gate-implement ${unit_id}"
    return
  fi
  if [[ "$(phase_state "$unit_id" "Evaluate gate passed")" != "done" ]]; then
    echo "Fill EVALUATE_NOTES.md and run: bash scripts/run_micro_cycle.sh run ${unit_id} ${stage}"
    return
  fi
  echo "Commit/push feature branch, fast-forward QA worktree, run canonical QA, and record evidence."
}

write_status_report() {
  local unit_id="$1"
  local stage="$2"
  local dir report
  dir="$(unit_dir "$unit_id")"
  mkdir -p "$dir/reports"
  report="$dir/reports/expert-agent-status-$(ts_now).md"
  cat >"$report" <<EOF
# Expert Agent Workflow Status

- unit_id: \`${unit_id}\`
- target_stage: \`${stage}\`
- next_owner: \`$(next_owner "$unit_id")\`
- generated_at_utc: \`$(ts_now)\`

## Phase State
- Plan: \`$(phase_state "$unit_id" "Plan gate passed")\`
- Review: \`$(phase_state "$unit_id" "Review gate passed")\`
- Implement: \`$(phase_state "$unit_id" "Implement gate passed")\`
- Evaluate: \`$(phase_state "$unit_id" "Evaluate gate passed")\`

## Next Command
\`$(next_command "$unit_id" "$stage")\`
EOF
  echo "$report"
}

prepare() {
  local unit_id="$1"
  local goal="$2"
  local stage="${3:-8}"
  if [[ ! -d "$(unit_dir "$unit_id")" ]]; then
    bash "$MICRO_CYCLE" init "$unit_id" "$goal" "$stage"
  fi
  require_unit "$unit_id"
  local report
  report="$(write_status_report "$unit_id" "$stage")"
  echo "[OK] prepared unit: $(unit_dir "$unit_id")"
  echo "[OK] next owner: $(next_owner "$unit_id")"
  echo "[OK] report: $report"
}

status_cmd() {
  local unit_id="$1"
  local stage="${2:-8}"
  require_unit "$unit_id"
  local report
  report="$(write_status_report "$unit_id" "$stage")"
  echo "[OK] next owner: $(next_owner "$unit_id")"
  echo "[OK] next command: $(next_command "$unit_id" "$stage")"
  echo "[OK] report: $report"
}

verify() {
  local unit_id="$1"
  local stage="${2:-8}"
  require_unit "$unit_id"
  bash "$MICRO_CYCLE" run "$unit_id" "$stage"
  local report
  report="$(write_status_report "$unit_id" "$stage")"
  echo "[OK] verify completed"
  echo "[OK] next owner: $(next_owner "$unit_id")"
  echo "[OK] report: $report"
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    prepare)
      [[ $# -ge 3 ]] || { usage; exit 1; }
      prepare "$2" "$3" "${4:-8}"
      ;;
    status)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      status_cmd "$2" "${3:-8}"
      ;;
    verify)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      verify "$2" "${3:-8}"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
