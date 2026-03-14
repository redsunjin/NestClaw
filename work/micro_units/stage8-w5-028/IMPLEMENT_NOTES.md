# Implement Notes

## Changed Files
- `app/services/orchestration_service.py`
- `app/static/agent-quickstart.html`
- `app/static/agent-quickstart.js`
- `app/static/agent-console.html`
- `app/static/agent-console.js`
- `app/static/agent-console.css`
- `tests/test_agent_entrypoint_smoke.py`
- `tests/test_web_console_runtime.py`
- `tests/test_stage8_contract.py`

## Implementation Summary
- recent task payload에 planner provenance 요약 필드(`planning_provider_id`, `planned_tool_ids`, `executed_tool_ids`)를 추가했다.
- quickstart에 `Planner` status card를 추가하고 current task의 planner source/provider/tool flow를 표시한다.
- console에 planner summary / plan detail panel을 추가해 current task의 planner provenance와 planned/executed action 흐름을 함께 보여준다.
- recent task 카드에도 planner label과 planned tool flow를 노출해 status 화면에 들어가기 전에도 plan 관측이 가능하게 했다.

## Rollback Plan
- recent payload 확장을 제거하고 `_agent_recent_item()`을 이전 필드 집합으로 되돌린다.
- quickstart/console의 planner UI panel을 제거하고 기존 status/report 중심 화면으로 복구한다.
- UI runtime/static tests에서 provenance 관련 assertion을 제거해 이전 surface 계약으로 되돌린다.

## Known Risks
- recent payload에 planner 요약이 늘어나 응답 크기가 약간 증가한다.
- planner summary 문자열은 UI 친화적이지만 long tool list일 때 가독성이 떨어질 수 있다.
- quickstart와 console이 유사한 formatter를 별도로 가지므로 후속 공통화 여지가 남아 있다.
