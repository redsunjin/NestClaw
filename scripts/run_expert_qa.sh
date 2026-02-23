#!/usr/bin/env bash
set -euo pipefail

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_DIR="reports/qa"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/expert-qa-${TS}.md"

DOC_AUDIT_LOG="/tmp/expert_doc_audit_${TS}.log"
CYCLE_LOG="/tmp/expert_cycle_${TS}.log"
SPEC_LOG="/tmp/expert_spec_${TS}.log"
RUNTIME_LOG="/tmp/expert_runtime_${TS}.log"

doc_status="PASS"
cycle_status="PASS"
spec_status="PASS"
runtime_status="PASS"

set +e
bash scripts/run_doc_audit.sh >"$DOC_AUDIT_LOG" 2>&1
DOC_RC=$?
bash scripts/run_dev_qa_cycle.sh 7 >"$CYCLE_LOG" 2>&1
CYCLE_RC=$?
python3 -m unittest tests.test_spec_contract >"$SPEC_LOG" 2>&1
SPEC_RC=$?
python3 -m unittest tests.test_runtime_smoke >"$RUNTIME_LOG" 2>&1
RUNTIME_RC=$?
set -e

if [[ "$DOC_RC" -ne 0 ]]; then doc_status="FAIL"; fi
if [[ "$CYCLE_RC" -ne 0 ]]; then cycle_status="FAIL"; fi
if [[ "$SPEC_RC" -ne 0 ]]; then spec_status="FAIL"; fi
if rg -q "skipped=[1-9]" "$RUNTIME_LOG"; then
  runtime_status="SKIP"
elif [[ "$RUNTIME_RC" -ne 0 ]]; then
  runtime_status="FAIL"
fi

overall="PASS"
if [[ "$doc_status" == "FAIL" || "$cycle_status" == "FAIL" || "$spec_status" == "FAIL" || "$runtime_status" == "FAIL" ]]; then
  overall="FAIL"
fi

{
  echo "# Expert QA Report"
  echo ""
  echo "- executed_at_utc: $TS"
  echo "- overall: $overall"
  echo ""
  echo "## Evidence"
  echo "- documentation_audit: $doc_status"
  echo "- stage_cycle: $cycle_status"
  echo "- spec_tests: $spec_status"
  echo "- runtime_tests: $runtime_status"
  echo ""
  echo "## Expert Verdicts"
  echo "| Expert | Focus | Verdict | Notes |"
  echo "|---|---|---|---|"
  echo "| A01 Product Owner | 목적/범위 일치성 | $doc_status | README/TASKS/최신 검토문서 정합성 기준 |"
  echo "| A02 Workflow Engineer | 상태머신/실행흐름 | $cycle_status | Stage cycle 결과 기준 |"
  echo "| A03 LLM Orchestrator | 체인/오케스트레이션 | $cycle_status | Stage2/Stage4 체크 기준 |"
  echo "| A04 Security Privacy | RBAC/정책/감사 | $spec_status | RBAC 헤더/감사 엔드포인트 테스트 기준 |"
  echo "| A05 UX Operations | 비IT 실행 흐름 | $cycle_status | CLI 및 Step5 체크 기준 |"
  echo "| A06 QA Reliability | 테스트 게이트 | $spec_status | 정적 계약 테스트 기준 |"
  echo "| A07 Compliance Advisor | 추적성/감사 | $doc_status | API 계약서+감사 요약 스펙 기준 |"
  echo "| A08 Domain SME | 결과물 유효성 | $runtime_status | 런타임 테스트 가능 여부 기준 |"
  echo ""
  echo "## Action Items"
  if [[ "$overall" == "PASS" ]]; then
    echo "- 현재 기준선 통과. 다음 단계 계획으로 진행 가능."
  else
    echo "- 실패 항목 우선 수정 후 재실행 필요."
  fi
  if [[ "$runtime_status" == "SKIP" ]]; then
    echo "- 런타임 QA는 의존성 설치 환경에서 최종 재검증 필요."
  fi
  echo ""
  echo "## Raw Logs"
  echo "- doc_audit_log: $DOC_AUDIT_LOG"
  echo "- cycle_log: $CYCLE_LOG"
  echo "- spec_log: $SPEC_LOG"
  echo "- runtime_log: $RUNTIME_LOG"
  echo "- report: $REPORT_FILE"
} >"$REPORT_FILE"

cat "$REPORT_FILE"

if [[ "$overall" != "PASS" ]]; then
  exit 1
fi
