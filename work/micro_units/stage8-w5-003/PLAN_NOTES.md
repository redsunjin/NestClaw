# Plan Notes

## Scope
- `app/services/` 패키지를 추가하고 agent/task/incident orchestration service를 분리한다.
- `app/main.py`의 agent/task/incident route handler를 얇은 adapter로 축소한다.
- 단일 service 계층이 CLI/MCP에서 재사용 가능한 구조가 되도록 request 해석/라우팅/상태 payload/CRUD orchestration을 이동한다.
- 기존 runtime smoke와 QA cycle이 회귀 없이 유지되도록 테스트를 그대로 통과시킨다.

## Out of Scope
- 실제 MCP server 구현
- 비대화형 CLI 구현
- LLM intent routing 연결
- pipeline executor/planner/reviewer/reporter 자체 로직의 재설계
- approval endpoint 분리

## Acceptance Criteria
- `app/services/orchestration_service.py`가 추가되고 agent/task/incident service 로직을 제공한다.
- `app/main.py` route handler는 service 호출 중심으로 축소된다.
- 기존 `/api/v1/agent/*`, `/api/v1/task/*`, `/api/v1/incident/*` 계약은 유지된다.
- `tests.test_spec_contract`, `tests.test_stage8_contract`, `tests.test_runtime_smoke`, `tests.test_agent_entrypoint_smoke`, `tests.test_incident_runtime_smoke`가 통과하거나 feature worktree에서는 dependency-gated skip으로 유지된다.
- `bash scripts/run_micro_cycle.sh run stage8-w5-003 8`가 통과한다.

## Risks
- service 계층이 main.py callback에 과도하게 의존하면 분리 효과가 약해질 수 있다.
- route/service 경계에서 request model과 dict payload가 혼재하면 회귀가 생길 수 있다.
- 잘못 분리하면 auth/policy/idempotency 흐름이 우회될 수 있다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_runtime_smoke tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke`
- 품질 게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-003 8`
