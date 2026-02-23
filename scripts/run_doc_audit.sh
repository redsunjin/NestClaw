#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="reports/audit"
mkdir -p "$REPORT_DIR"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_FILE="$REPORT_DIR/doc-audit-${TS}.md"

PASS=0
FAIL=0

pass() {
  PASS=$((PASS + 1))
  echo "- [PASS] $1" | tee -a "$REPORT_FILE"
}

fail() {
  FAIL=$((FAIL + 1))
  echo "- [FAIL] $1" | tee -a "$REPORT_FILE"
}

check_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    pass "file exists: $f"
  else
    fail "file missing: $f"
  fi
}

check_pattern_in_file() {
  local file="$1"
  local pattern="$2"
  local title="$3"
  if rg -q "$pattern" "$file"; then
    pass "$title"
  else
    fail "$title"
  fi
}

{
  echo "# Documentation Audit Report"
  echo ""
  echo "- executed_at_utc: $TS"
  echo ""
  echo "## Checks"
} >"$REPORT_FILE"

# Core docs
check_file "README.md"
check_file "TASKS.md"
check_file "API_CONTRACT.md"
check_file "EXPERT_REVIEW_UPDATE_2026-02-24.md"
check_file "SECURE_AGENT_COLLAB_ARCHITECTURE.md"
check_file "CODEX_AUTOMATION_CYCLE.md"

# API contract vs implementation
check_pattern_in_file "API_CONTRACT.md" 'POST `/api/v1/task/create`' "contract includes create endpoint"
check_pattern_in_file "API_CONTRACT.md" 'POST `/api/v1/task/run`' "contract includes run endpoint"
check_pattern_in_file "API_CONTRACT.md" 'GET `/api/v1/task/status/\{task_id\}`' "contract includes status endpoint"
check_pattern_in_file "API_CONTRACT.md" 'GET `/api/v1/task/events/\{task_id\}`' "contract includes events endpoint"
check_pattern_in_file "API_CONTRACT.md" 'GET `/api/v1/audit/summary`' "contract includes audit endpoint"

check_pattern_in_file "app/main.py" "def create_task" "implementation has create endpoint"
check_pattern_in_file "app/main.py" "def run_task" "implementation has run endpoint"
check_pattern_in_file "app/main.py" "def task_status" "implementation has status endpoint"
check_pattern_in_file "app/main.py" "def task_events" "implementation has events endpoint"
check_pattern_in_file "app/main.py" "def audit_summary" "implementation has audit endpoint"

# RBAC and QA references
check_pattern_in_file "README.md" "X-Actor-Role" "readme documents RBAC header"
check_pattern_in_file "README.md" "scripts/run_auto_cycle.sh" "readme documents auto cycle script"
check_pattern_in_file "TASKS.md" "Step 6" "tasks include QA gate step"
check_pattern_in_file "TASKS.md" "\\[x\\] RBAC 역할 정의" "tasks show RBAC completed"

{
  echo ""
  echo "## Summary"
  echo "- pass: $PASS"
  echo "- fail: $FAIL"
  echo "- report: $REPORT_FILE"
} | tee -a "$REPORT_FILE"

if [[ "$FAIL" -gt 0 ]]; then
  echo "Documentation audit failed."
  exit 1
fi

echo "Documentation audit passed."
