# Implement Notes

## Changed Files
- `app/runtime_taxonomy.py`
- `app/services/capability_manifest_service.py`
- `app/services/orchestration_service.py`
- `app/cli.py`
- `app/static/agent-console.js`
- `app/static/agent-console.html`
- `app/static/agent-quickstart.js`
- `app/static/agent-quickstart.html`
- `tests/test_capability_manifest_runtime.py`
- `tests/test_agent_entrypoint_smoke.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_web_console_runtime.py`
- `tests/test_stage10_contract.py`
- `work/micro_units/stage10-w1-003/PLAN_NOTES.md`
- `work/micro_units/stage10-w1-003/REVIEW_NOTES.md`

## Rollback Plan
- canonical taxonomy는 additive field 중심 변경이라, 문제가 생기면 `app/runtime_taxonomy.py` 호출과 surface summary 노출만 제거하면 기존 status/readiness 구조로 쉽게 돌아갈 수 있다.
- HTTP/CLI/MCP의 기존 `status`, `approval_reason`, `missing_env` 필드는 유지했으므로, 새 `state_summary`와 readiness canonical fields를 되돌려도 소비자 계약의 기본 경로는 남는다.
- UI 변경도 summary/chip 수준이라, 필요 시 JS helper와 asset version만 되돌리면 operator surface는 기존 레이아웃으로 복귀한다.

## Known Risks
- canonical reason code는 현재 Stage 10 범위에 맞는 최소 vocabulary만 담았기 때문에, 이후 더 많은 adapter/runtime failure class가 생기면 분류표를 확장해야 한다.
- `FAILED_RETRYABLE`의 detail reason은 현재 `last_error` 문자열을 단순 정규화하므로 세밀한 오류 분류는 아직 제한적이다.
- readiness는 외부 env block만 taxonomy로 올렸고, live rehearsal 결과의 richer failure class까지는 아직 확장하지 않았다.
