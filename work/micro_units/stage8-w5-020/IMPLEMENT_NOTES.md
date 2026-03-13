# Implement Notes

## Changed Files
- `app/services/orchestration_service.py`
  - report path 권한/루트 검증과 `agent_report`, `agent_report_path` access helper를 추가한다.
- `app/main.py`
  - `GET /api/v1/agent/report/{task_id}` 및 `/raw` route를 추가한다.
- `app/static/agent-console.html`
  - 실행 상태 패널에 report preview / raw open 버튼과 preview 카드 영역을 추가한다.
- `app/static/agent-console.js`
  - recent task/current task 기준 report preview, raw open, auto preview 동선을 추가한다.
- `app/static/agent-console.css`
  - report preview card 스타일을 추가한다.
- `README.md`, `TASKS.md`, `API_CONTRACT.md`, `NEXT_WORK_GROUPS_2026-03-13.md`
  - operator surface 현재 기능과 다음 후보를 갱신한다.
- `tests/test_agent_entrypoint_smoke.py`, `tests/test_web_console_runtime.py`, `tests/test_stage8_contract.py`
  - report access auth, web console wiring, contract surface를 회귀 테스트로 고정한다.

## Rollback Plan
- `agent_report` / `agent_report_raw` route와 service helper를 제거한다.
- Web Console의 report preview / raw open 버튼과 preview 카드를 제거하고 기존 status/events 흐름만 유지한다.
- README/TASKS/API_CONTRACT/NEXT_WORK_GROUPS에서 report preview 관련 문구를 제거한다.

## Known Risks
- raw report open은 browser popup 정책에 영향을 받을 수 있다. 현재는 직접 클릭 이벤트에서만 실행하도록 맞췄다.
- preview는 문자 수 기준 truncate라 markdown 단락 중간에서 끊길 수 있다.
- report path 검증은 `reports/` root를 기준으로 하므로 향후 외부 storage로 옮기면 별도 adapter가 필요하다.
