#!/usr/bin/env bash
set -euo pipefail

PLAN_FILE="${1:-NEXT_STAGE_PLAN_2026-02-24.md}"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_DIR="reports/qa"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/plan-qa-${TS}.md"

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

require_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    pass "plan file exists: $file"
  else
    fail "plan file missing: $file"
  fi
}

require_pattern() {
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
  echo "# Plan QA Report"
  echo ""
  echo "- plan_file: $PLAN_FILE"
  echo "- executed_at_utc: $TS"
  echo ""
  echo "## Checks"
} >"$REPORT_FILE"

require_file "$PLAN_FILE"

if [[ -f "$PLAN_FILE" ]]; then
  require_pattern "$PLAN_FILE" "^## 목표" "contains goal section"
  require_pattern "$PLAN_FILE" "^## Stage 7 범위" "contains scope section"
  require_pattern "$PLAN_FILE" "^## 완료 기준" "contains acceptance criteria"
  require_pattern "$PLAN_FILE" "^## 실행 순서" "contains execution order"
  require_pattern "$PLAN_FILE" "^## 리스크" "contains risk section"
  require_pattern "$PLAN_FILE" "^## 대응" "contains mitigation section"

  require_pattern "$PLAN_FILE" "JWT|SSO|인증" "covers authentication upgrade"
  require_pattern "$PLAN_FILE" "DB|SQLite|PostgreSQL|영속" "covers persistence migration"
  require_pattern "$PLAN_FILE" "CI|게이트|품질" "covers CI quality gate"
fi

{
  echo ""
  echo "## Summary"
  echo "- pass: $PASS"
  echo "- fail: $FAIL"
  echo "- report: $REPORT_FILE"
} | tee -a "$REPORT_FILE"

if [[ "$FAIL" -gt 0 ]]; then
  echo "Plan QA failed."
  exit 1
fi

echo "Plan QA passed."
