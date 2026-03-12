# Implement Notes

## Changed Files
- `app/slack_adapter.py`
- `app/services/tool_draft_service.py`
- `app/main.py`
- `app/cli.py`
- `app/mcp_server.py`
- `app/services/__init__.py`
- `app/services/orchestration_service.py`
- `configs/tool_registry.yaml`
- `tests/test_slack_adapter_contract.py`
- `tests/test_tool_draft_runtime.py`
- `tests/test_tool_registry_contract.py`
- `tests/test_tool_registry_runtime.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_stage8_contract.py`

## Rollback Plan
- Revert the MWU commit to remove Slack and tool draft surfaces together.
- If only draft surfaces need rollback, remove `/api/v1/tool-drafts`, `tool-draft`, and `catalog.create_draft/get_draft` while keeping Slack catalog support.

## Known Risks
- tool draft generation is heuristic and intentionally conservative; non-Slack tools may still need manual field correction before review.
- Slack planned action currently composes its message before any Redmine external reference exists.
