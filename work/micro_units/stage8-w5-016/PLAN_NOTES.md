# Plan Notes

## Scope
- 기존 Web Console에 `agent.submit`, `agent.status`, `agent.events` 흐름을 추가한다.
- 브라우저에서 바로 눌러볼 수 있도록 task/incident 예시 입력을 제공한다.
- backend API 계약은 바꾸지 않고 static UI만 확장한다.

## Out of Scope
- planner/tool execution backend 로직 추가
- approval 처리 UI
- 다중 task 히스토리 저장 또는 세션 기반 대시보드

## Acceptance Criteria
- Console에서 자연어 요청을 제출할 수 있다.
- 응답의 `task_id`가 자동으로 상태 조회 필드에 채워진다.
- status/events를 같은 화면에서 확인할 수 있다.
- 관련 runtime smoke와 contract 검사가 추가된다.

## Risks
- metadata JSON 입력이 잘못되면 브라우저 쪽에서 에러가 날 수 있으므로 명확히 표시해야 한다.
- auto task kind 예시는 intent classifier fallback/runtime 차이에 따라 결과가 달라질 수 있다.
- UI만 넓히고 operator 정보 구조가 없으면 화면이 금방 복잡해질 수 있다.

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_agent_entrypoint_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-016`
- 구현 후 `bash scripts/run_micro_cycle.sh run stage8-w5-016 8`
