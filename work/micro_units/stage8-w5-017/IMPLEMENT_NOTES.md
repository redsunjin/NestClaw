# Implement Notes

## Changed Files
- `app/static/agent-console.html`
- `app/static/agent-console.css`
- `app/static/agent-console.js`
- `tests/test_web_console_runtime.py`
- `tests/test_stage8_contract.py`
- `README.md`

## Rollback Plan
- approval panel만 문제면 Web Console에서 해당 섹션과 JS 액션만 제거하면 된다.
- backend approval API는 바꾸지 않았으므로 rollback은 정적 자산과 문서 범위에 머문다.

## Known Risks
- approval panel은 수동 refresh 기반이라 동시 작업자가 많으면 상태가 바로 반영되지 않을 수 있다.
- 현재 UI는 최근 task 중심이라 여러 승인 요청을 한꺼번에 다루는 운영 대시보드는 아니다.
