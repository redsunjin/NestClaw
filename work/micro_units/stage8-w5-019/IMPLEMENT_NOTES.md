# Implement Notes

## Changed Files
- `app/services/orchestration_service.py`
  - `agent_recent()`와 recent item payload helper를 추가해 최근 task 히스토리 API를 제공한다.
- `app/main.py`
  - `GET /api/v1/agent/recent` 표면을 추가해 actor role별 recent task 조회를 노출한다.
- `app/static/agent-console.html`
  - 최근 task / 최근 approval 히스토리 패널을 추가한다.
- `app/static/agent-console.js`
  - recent task 조회, recent approval 조회, recent task 클릭 시 status/events 로드 동선을 추가한다.
- `app/static/agent-console.css`
  - history card/grid 스타일과 mobile 대응 레이아웃을 추가한다.
- `API_CONTRACT.md`, `README.md`, `TASKS.md`, `NEXT_WORK_GROUPS_2026-03-13.md`
  - operator surface 확장과 grouped next-work 계획을 문서 기준으로 고정한다.
- `tests/test_agent_entrypoint_smoke.py`, `tests/test_web_console_runtime.py`, `tests/test_stage8_contract.py`
  - recent API 권한, web console history panel, grouped plan 문서를 회귀 테스트로 고정한다.

## Rollback Plan
- `/api/v1/agent/recent` route와 `OrchestrationService.agent_recent()`를 제거한다.
- Web Console의 history panel 관련 DOM, JS, CSS를 제거하고 기존 approval/task 패널만 유지한다.
- `NEXT_WORK_GROUPS_2026-03-13.md`와 관련 README/TASKS/API 문서 링크를 제거한다.

## Known Risks
- requester role에서는 recent task만 조회 가능하므로 approval history 버튼은 403을 받을 수 있다. 이는 기존 approval 정책 유지에 따른 의도된 제한이다.
- recent task 정렬은 `updated_at` 기준 문자열 정렬이므로 clock skew가 있는 경우 기대와 다를 수 있다.
- history panel은 조회 표면만 추가한 것이며 report preview, approval comment drill-down은 후속 G1 범위다.
