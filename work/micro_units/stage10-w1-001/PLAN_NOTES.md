# Plan Notes

## Scope
- orchestration service에 `agent_bundle` payload를 추가해 `status`, `events`, `report preview`, `approval snapshot`, `capability manifest summary`를 하나의 task-scoped export로 묶는다.
- HTTP, non-interactive CLI, MCP에 동일한 bundle 조회 표면을 추가한다.
- approval detail 접근 권한이 없는 actor는 limited summary만 받고, approver/admin은 approval detail/history까지 bundle에 포함받도록 권한별 분기를 둔다.
- stage10 contract/runtime test를 추가해 bundle shape와 surface parity를 고정한다.

## Out of Scope
- planner/executor 로직 변경
- 새로운 live capability 추가
- dashboard chat panel 구현
- Stage 8 sandbox/live env 확보 또는 readiness 상태 변경
- report 포맷 자체 변경

## AI-First Planner Design
- 이번 단위는 planner intelligence 확장이 아니라 `AI planner 결과를 어떻게 export/handoff 할 것인가`를 다룬다.
- task/incident 모두 이미 가진 `planning_provenance`, `planned_actions`, `action_results`를 bundle에서 재사용하고, upper agent는 별도 heuristic 없이 canonical bundle만 읽도록 유도한다.
- execution bundle은 planner를 우회하는 새 경로가 아니라 기존 `agent.status/events/report`, `approval.*`, `capabilities`를 읽기 전용으로 조합한 contract다.
- 따라서 planner source, degraded mode, approval gate, audit trail은 기존 runtime semantics를 유지한 채 더 읽기 쉽게 묶이는 것이 목표다.

## Acceptance Criteria
- `app/services/orchestration_service.py`에 task-scoped execution bundle export가 추가된다.
- HTTP `GET /api/v1/agent/bundle/{task_id}`, CLI `newclaw bundle`, MCP `agent.bundle`이 같은 canonical bundle shape를 반환한다.
- bundle은 최소 `status`, `events`, `report`, `approval`, `capabilities` 섹션을 포함한다.
- requester/reviewer는 approval summary까지만, approver/admin은 approval detail/history까지 접근 가능하다.
- `tests.test_tool_cli_smoke`, `tests.test_mcp_server_smoke`, 신규 runtime/contract test가 통과한다.

## Risks
- bundle에 capability manifest를 포함하면 payload가 커질 수 있어, 요약 수준과 raw detail 범위를 분리해야 한다.
- approval detail을 무심코 requester에게 노출하면 role policy 회귀가 된다.
- status/events/report payload를 중복 조합하는 과정에서 field naming drift가 생기면 upper-agent integration이 오히려 불안정해질 수 있다.
- report가 없는 상태에서도 bundle이 호출될 수 있으므로 partial availability shape를 명확히 유지해야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage10-w1-001`
- `bash scripts/run_micro_cycle.sh gate-review stage10-w1-001`
- `python3 -m unittest tests.test_stage10_contract tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
- `python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_runtime_smoke`
- `bash scripts/run_micro_cycle.sh gate-implement stage10-w1-001`
- `bash scripts/run_micro_cycle.sh run stage10-w1-001 10`
