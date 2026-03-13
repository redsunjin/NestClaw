# Implement Notes

## Changed Files
- `app/main.py`
- `app/static/agent-console.html`
- `app/static/agent-console.css`
- `app/static/agent-console.js`
- `tests/test_web_console_runtime.py`
- `tests/test_stage8_contract.py`
- `README.md`

## Rollback Plan
- 루트 UI가 문제를 만들면 `app/main.py`의 `/` route와 `/static` mount를 제거하고 `app/static/` 자산을 되돌리면 된다.
- core orchestration/service 계층은 건드리지 않았으므로 rollback 범위는 UI adapter와 문서로 제한된다.

## Known Risks
- 현재 UI는 개발 모드 호환 헤더를 직접 넣는 최소 콘솔이라 production auth/SSO UX를 대체하지 않는다.
- 클라이언트 측 fetch 기반이라 operator workflow가 늘어나면 별도 frontend 구조로 분리할 필요가 있다.
