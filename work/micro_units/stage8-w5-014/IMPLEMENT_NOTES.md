# Implement Notes

## Changed Files
- `app/tool_registry.py`
- `app/services/tool_draft_service.py`
- `app/main.py`
- `app/cli.py`
- `app/mcp_server.py`
- `tests/runtime_test_utils.py`
- `tests/test_tool_registry_contract.py`
- `tests/test_tool_draft_runtime.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_stage8_contract.py`

## Rollback Plan
- Revert the MWU commit to disable draft apply and remove overlay support together.
- Delete `work/tool_registry_runtime.yaml` if rollback is done after a local apply rehearsal.

## Known Risks
- overlay registry는 append/replace 수준만 지원한다. 삭제나 rename workflow는 아직 없다.
- draft parser는 현재 서비스가 생성한 yaml 형식을 기준으로 한다.
