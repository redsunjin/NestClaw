# Plan Notes

## Scope
- `app/main.py`에 incident 전용 입력/실행 경로를 추가한다.
- 기존 task 파이프라인과 충돌하지 않도록 incident 경로는 feature-flag 기반 dry-run 모드로 시작한다.
- `tests/test_incident_runtime_smoke.py`를 추가해 정상/승인대기/차단/실패복구의 최소 경로를 검증한다.
- Stage 8 계약 문서와 상태머신 규칙을 위배하지 않도록 `TaskStatus` 전이를 재사용한다.

## Out of Scope
- Redmine live 호출/외부 RAG live 네트워크 연동
- Sandbox 실환경 데이터 검증
- CI 파이프라인의 Stage 8 강제 게이트 반영(별도 MWU)

## Acceptance Criteria
- incident 경로가 기존 `/api/v1/task/*` 경로와 독립적으로 동작한다.
- dry-run incident 실행 시 action card 생성/게이트 판정/리포트 작성이 재현된다.
- 정책 위반 입력은 `BLOCKED_POLICY` 또는 승인 큐 전환으로 처리된다.
- `tests/test_incident_runtime_smoke.py`가 통과한다.
- `bash scripts/run_dev_qa_cycle.sh 8` 실행 시 fail 0을 유지한다.

## Risks
- 상태 전이 충돌로 기존 task 런타임 회귀 위험
- incident 경로와 approval 큐 공유 시 side effect 위험
- 테스트 fixture 복잡도 증가로 maintenance 비용 증가 위험

## Test Plan
- 단위/계약:
  - `python3 -m unittest tests.test_incident_adapter_contract`
  - `python3 -m unittest tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_incident_runtime_smoke`
- 통합:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_stage8_self_eval.sh`
