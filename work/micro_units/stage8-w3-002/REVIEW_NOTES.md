# Review Notes

## Security / Policy Review
- 승인 분류의 기준은 `STAGE8_DETAILED_DESIGN_2026-03-04.md` 5.4 표와 추가 규칙을 우선한다.
- 정책 위반(`external_send_requested`)은 risk 판정보다 먼저 차단되어야 한다.
- approval queue에는 사람에게 설명 가능한 `reason_message`를 남겨 운영자가 원인을 파악할 수 있어야 한다.
- critical risk는 자동 실행 금지이며 최소 `two_person_review_recommended` 증적을 남긴다.

## Architecture / Workflow Review
- 정책 룰은 `app/main.py`에서 분리해 순수 함수/데이터 중심 모듈로 유지한다.
- incident runtime은 정책 모듈의 결정 결과만 사용하고, queue 생성/상태 전이는 기존 orchestrator가 담당한다.
- 기존 task 정책 차단 경로는 회귀 없이 동일 reason code를 유지한다.
- G3 구현은 G2 런타임 경로를 깨지 않도록 static/unit test 우선으로 검증한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_incident_policy_gate`
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
  - `bash scripts/run_micro_cycle.sh run stage8-w3-002 8`
- 필요 시 QA worktree에서 Stage 8 self-eval을 재실행해 G3 그룹 판정을 확인한다.

## Review Verdict
- 조건부 승인 (Approved with Guardrails)
- 조건:
  1. `reason_code`는 기존 API/runtime smoke와 호환되어야 한다.
  2. task 경로의 정책 차단 동작을 회귀시키면 안 된다.
  3. critical risk는 승인 필수 + 2인 검토 권고 증적을 남겨야 한다.
