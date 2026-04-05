# Implement Notes

## Changed Files
- `app/static/agent-console.html`
- `app/static/agent-console.js`
- `app/static/agent-console.css`
- `app/static/agent-quickstart.html`
- `app/static/agent-quickstart.js`
- `app/static/agent-quickstart.css`
- `tests/test_web_console_runtime.py`
- `work/micro_units/stage10-w1-002/PLAN_NOTES.md`
- `work/micro_units/stage10-w1-002/REVIEW_NOTES.md`

## Rollback Plan
- role gating은 UI 표면 변경이라 backend contract를 건드리지 않았다.
- 문제가 생기면 quickstart/console의 `data-role-scope`, JS runtime guard, role-specific copy만 되돌리면 기존 API/RBAC는 그대로 유지된다.
- CSS 변경도 `is-role-hidden`과 role summary styling 수준이라, UI가 어색하면 관련 selector만 제거해 바로 복구할 수 있다.

## Known Risks
- current role gating은 UI 중심이라, 사용자에게는 안전하지만 backend permission 모델 자체를 대체하지는 않는다.
- requester에게 draft authoring을 그대로 보여두었기 때문에, 여전히 secondary governance surface의 존재감이 남아 있을 수 있다.
- run mode option 잠금은 시각적 가이드이므로, 이후 backend policy와 vocabulary가 달라지면 문구를 다시 맞춰야 한다.
