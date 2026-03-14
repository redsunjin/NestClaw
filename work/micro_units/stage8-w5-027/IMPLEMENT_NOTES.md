# Implement Notes

## Changed Files
- `app/main.py`
- `tests/test_agent_planner_runtime.py`
- `tests/test_stage8_contract.py`

## Implementation Summary
- common executor에 cross-action binding helper를 추가해 앞선 action result를 뒤 action payload에 주입할 수 있게 했다.
- `summary -> ticket -> slack` task plan에서 `{{summary_output}}`, `{{summary_excerpt}}` token을 사용하도록 payload template를 바꿨다.
- task executor를 순차 실행으로 전환해 각 action이 직전 결과를 binding context로 참조하게 했다.
- incident executor도 같은 `prior_results` interface를 사용하도록 맞춰 공통 planner-executor 계약을 유지했다.
- action result에 `request_payload`를 남겨 QA와 audit가 실제 binding 결과를 확인할 수 있게 했다.

## Rollback Plan
- `app/main.py`의 binding helper와 sequential execution loop를 되돌려 기존 direct payload dispatch로 복구한다.
- binding placeholder를 제거해 ticket/slack payload를 정적 텍스트로 되돌린다.
- 회귀 시 `tests/test_agent_planner_runtime.py`의 binding assertion을 제거하고 이전 smoke contract를 복원한다.

## Known Risks
- summary output이 길 경우 downstream payload가 커질 수 있다. 현재는 slack preview에 excerpt 규칙을 둬 완화했다.
- request payload를 result에 남기므로 응답 크기가 약간 증가한다.
- token replacement는 allowlisted placeholder에 한정돼 있지만, richer structured binding은 아직 지원하지 않는다.
