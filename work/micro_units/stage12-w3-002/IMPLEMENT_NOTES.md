# Implement Notes

## Changed Files
- `app/mcp_server.py`: added MCP tools `job.list`, `job.describe`, and `job.run`.
- `app/stage12_jobs.py`: reused by MCP handlers for shared Stage 12 job contract.
- `tests/test_mcp_server_smoke.py`: added tools/list coverage and MCP job discovery/run smoke.
- `app/services/capability_manifest_service.py`: added `job.*` tools to upper-agent-safe controls and updated primary entrypoint.
- `tests/test_capability_manifest_runtime.py` and `tests/test_tool_cli_smoke.py`: updated manifest expectations for job surfaces.
- Stage 12 docs and integration examples updated with MCP job usage.

## Rollback Plan
- Remove `job.*` ToolSpec entries and handlers from `app/mcp_server.py`.
- Remove `job.*` controls from capability manifest service.
- Remove MCP smoke assertions and MCP docs.

## Known Risks
- MCP remains stdio-only; remote gateway is still future work.
- `job.run` returns complete evidence synchronously, so long-running future jobs may require a separate async contract.
