# Plan Notes

## Scope
- `incident` workflow에도 `planning_provenance`를 도입해 task/incident가 같은 planner-executor 관측 계약을 공유하게 만든다.
- incident path의 planned action builder를 helper로 분리하고, `eligible_tools`, `selected_tools`, `source`, `provider_selection`을 provenance에 기록한다.
- incident status/event에서 planner 생성 사실을 확인할 수 있게 `INCIDENT_PLAN_GENERATED` 계열 이벤트를 추가한다.
- 기존 `action_cards`와 `planned_actions` 양쪽 표면은 유지해 하위 호환을 지킨다.

## Out of Scope
- incident path를 LLM planner로 전환하는 작업
- incident provider/RAG live reasoning 확장
- cross-action data binding
- operator UI 변경

## AI-First Planner Design
- 현재 incident는 deterministic planner로 유지하지만, task와 같은 `planned_actions + planning_provenance` 계약으로 수렴시킨다.
- provenance 구조는 task와 유사하게 `source`, `rationale`, `confidence`, `provider_selection`, `eligible_tools`, `degraded_mode`를 가진다.
- incident path의 초기 source는 `deterministic_incident_planner`로 고정한다.
- 이후 incident AI planner가 들어와도 status/event/API 계약을 바꾸지 않도록 이번 단계에서 공통 계약을 먼저 고정한다.

## Acceptance Criteria
- incident runtime status 응답에 `planning_provenance`가 포함된다.
- incident done/approval 경로에서 `planned_actions`와 `planning_provenance`가 모두 유지된다.
- incident event log에 `INCIDENT_PLAN_GENERATED`가 남고 선택된 tool 수와 source를 확인할 수 있다.
- incident runtime smoke와 stage 8 contract가 통과한다.
- QA canonical cycle이 통과한다.

## Risks
- incident path는 approval gate가 action 단위로 동작하므로 planner provenance 추가 시 이벤트/상태 순서가 기존 테스트와 충돌할 수 있다.
- task/incident 공통 계약을 맞추는 과정에서 기존 `action_cards` 기반 도메인 테스트가 깨질 수 있다.
- provenance에 provider selection을 넣을 때 incident provider selection 시점과 planning 시점의 순서가 틀어지면 감사 로그 해석이 애매해질 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-026`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-026`
- `python3 -m unittest tests.test_incident_runtime_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-026 8`
