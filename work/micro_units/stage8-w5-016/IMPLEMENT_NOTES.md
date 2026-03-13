# Implement Notes

## Changed Files
- `app/static/agent-console.html`
- `app/static/agent-console.css`
- `app/static/agent-console.js`
- `tests/test_web_console_runtime.py`
- `tests/test_stage8_contract.py`
- `README.md`

## Rollback Plan
- agent submit/status/events UI만 문제라면 static console의 해당 섹션과 JS 호출부를 제거하면 된다.
- backend contract는 바꾸지 않았으므로 rollback 범위는 정적 자산과 문서에 한정된다.

## Known Risks
- metadata JSON 입력은 사용자가 잘못 적으면 클라이언트 단에서 실패한다.
- console은 최근 task 하나만 다루므로 다중 실행을 관리하는 운영 대시보드는 아직 아니다.
