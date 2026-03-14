# Plan Notes

## Scope
- multi-step executor에 cross-action data binding을 추가해 앞 action 결과를 뒤 action payload에 주입할 수 있게 만든다.
- 첫 적용 범위는 task workflow다. `summary -> ticket -> slack` 경로에서 summary output을 follow-up payload에 반영한다.
- 공통 executor helper를 incident path에서도 재사용 가능하게 만들고, 아직 binding을 쓰지 않는 incident path에도 같은 execution context interface를 적용한다.
- action result에 resolved/request payload 일부를 남겨 QA와 audit가 실제 binding 결과를 확인할 수 있게 만든다.

## Out of Scope
- incident LLM planner 도입
- summary 결과를 구조화 JSON으로 다시 파싱하는 고급 binding
- UI 변경
- live RAG/provider 확대

## AI-First Planner Design
- planner는 tool 순서를 고르고, executor는 실행 시점에 action 간 데이터를 바인딩한다.
- 이번 단계에서는 planner 출력 계약을 바꾸지 않고, executor가 `{{summary_output}}`, `{{summary_excerpt}}` 같은 binding token을 해석한다.
- degraded mode와 live planner 모두 같은 binding 규칙을 사용해야 한다.
- binding은 deterministic helper로 수행하고, 미해결 token이 남아도 안전한 기본값으로 실행 가능해야 한다.

## Acceptance Criteria
- task runtime에서 ticket action payload description이 summary output을 포함한다.
- task runtime에서 slack action payload text가 summary 기반 메시지로 해석된다.
- incident path도 같은 executor context signature를 사용하고 회귀 없이 통과한다.
- action_results 또는 execution result에 resolved/request payload가 남아 QA에서 binding 결과를 확인할 수 있다.
- stage 8 micro-cycle과 QA canonical cycle이 통과한다.

## Risks
- binding token을 과도하게 일반화하면 임의 문자열 치환으로 이어질 수 있다.
- request payload를 action_results에 너무 많이 남기면 로그/응답 크기가 커질 수 있다.
- summary output이 길어 후속 payload 길이를 넘을 수 있으므로 excerpt 규칙이 필요하다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-027`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-027`
- `python3 -m unittest tests.test_agent_planner_runtime tests.test_incident_runtime_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-027 8`
