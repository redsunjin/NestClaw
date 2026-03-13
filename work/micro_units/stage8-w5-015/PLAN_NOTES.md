# Plan Notes

## Scope
- 서버 루트 `/`에 사람이 보기 쉬운 최소 Web Console 1장을 추가한다.
- Console은 기존 API를 그대로 호출하며 도구 목록 조회, tool draft 생성, draft 조회/적용만 제공한다.
- 추가 UI는 로컬 개발 모드의 호환 헤더(`X-Actor-Id`, `X-Actor-Role`)를 사용한다.

## Out of Scope
- 새로운 planner/tool execution 로직 추가
- 전용 로그인 화면 또는 별도 세션 관리
- production-grade operator console 전체 설계

## Acceptance Criteria
- `GET /`가 HTML 콘솔을 반환한다.
- 브라우저에서 `/api/v1/tools`, `/api/v1/tool-drafts`, `/api/v1/tool-drafts/{draft_id}/apply` 흐름을 같은 화면에서 호출할 수 있다.
- 정적 asset과 root route에 대한 runtime smoke가 추가된다.
- README에 가장 쉬운 확인 경로가 반영된다.

## Risks
- 브라우저 UI가 개발용 헤더 흐름에 의존하므로 production auth 대체물이 아님
- static asset 경로를 잘못 연결하면 서버 기동 시 import 단계에서 실패할 수 있음
- UI 범위를 넓히면 operator console 전체 작업으로 번질 수 있으므로 1장으로 제한해야 함

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_tool_draft_runtime tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-015`
- 구현 후 `bash scripts/run_micro_cycle.sh run stage8-w5-015 8`
