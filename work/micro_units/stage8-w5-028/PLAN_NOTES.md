# Plan Notes

## Scope
- quickstart와 console UI에 planner provenance 요약을 추가해 현재 task가 어떤 planner source와 provider로 어떤 tool들을 골랐는지 바로 보이게 만든다.
- recent task payload를 약간 확장해 recent card에서도 planning source, provider, selected tool list를 바로 렌더링할 수 있게 만든다.
- current task status panel에는 `planning_provenance`, `planned_actions`, `action_results` 기반 plan summary를 노출한다.
- incident/task 모두 같은 UI renderer를 쓰되, source가 `llm`, `heuristic_fallback`, `deterministic_incident_planner`일 때 각각 읽기 쉬운 문구를 보여준다.

## Out of Scope
- auto-refresh/polling 추가
- 새로운 planner/executor backend 로직 추가
- tool governance lifecycle 변경
- live rehearsal 또는 sandbox env 작업

## AI-First Planner Design
- UI는 planner provenance를 first-class surface로 취급해야 한다. 즉 current task를 볼 때 planner source와 selected tools가 status보다 뒤에 숨지 않아야 한다.
- LLM path가 주 경로이므로 `llm` source일 때 provider id와 confidence를 우선 노출하고, `heuristic_fallback`은 degraded mode로 명시한다.
- incident deterministic planner도 같은 provenance card에 포함해 task/incident를 하나의 orchestration language로 읽게 만든다.
- selected tools는 planner output, executed tools는 action result로 구분해서 보여준다.

## Acceptance Criteria
- `GET /api/v1/agent/recent` 응답에 planner provenance UI에 필요한 요약 필드가 포함된다.
- quickstart에서 current task의 planner source/provider/tool selection을 확인할 수 있다.
- advanced console에서 current task 및 recent task 카드에 planner provenance와 selected tools가 표시된다.
- static/runtime UI tests가 새 planner provenance surface를 검증한다.
- stage 8 micro-cycle과 QA canonical cycle이 통과한다.

## Risks
- recent payload에 planner 정보를 과도하게 넣으면 history 응답이 커질 수 있으므로 요약 필드만 노출해야 한다.
- provider/fallback 문구가 UI에서 오해를 주지 않도록 LLM/degraded labeling을 명확히 해야 한다.
- planned tools와 executed tools를 혼동하면 operator가 잘못 이해할 수 있으므로 표시 라벨을 분리해야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-028`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-028`
- `python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_web_console_runtime tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-028 8`
