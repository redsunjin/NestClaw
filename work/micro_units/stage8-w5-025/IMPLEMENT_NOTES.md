# Implement Notes

## Changed Files
- `app/agent_planner.py`
- `app/main.py`
- `tests/test_agent_planner_contract.py`
- `tests/test_agent_planner_runtime.py`
- `tests/test_stage8_contract.py`

## Rollback Plan
- task path에서 `redmine.issue.create` helper와 eligibility provenance를 제거하고, planner 후보군을 다시 `summary + slack` baseline으로 축소한다.
- planner dataclass의 `eligible_tools` 필드가 회귀를 만들면 해당 필드만 제거하고 기존 action/provenance 계약으로 복귀한다.
- QA runtime에서 ticket dry-run path만 문제면 `NEWCLAW_TASK_TICKET_TOOL_ID` 경로를 비활성화하고 기존 planner baseline을 유지한다.

## Known Risks
- ticket payload는 현재 raw task input 기반이라 summary 결과를 직접 참조하는 richer follow-up 품질은 아직 부족하다.
- eligibility 기준이 request_text 힌트와 metadata에 의존하므로, 표현이 너무 모호한 요청은 ticket tool 후보군에 못 들어갈 수 있다.
- task path에서 redmine dry-run을 추가하면서 runtime smoke가 더 넓어졌으므로 QA 환경에서만 드러나는 회귀가 있을 수 있다.
