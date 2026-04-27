# Plan Notes

## Scope
- Add MCP tools for Stage 12 job discovery and invocation.
- Tools must cover `job.list`, `job.describe`, and `job.run`.
- Reuse the same Stage 12 job contract helper as CLI and HTTP.
- Runtime response must preserve status/events/report/bundle/handoff evidence shape.

## Out of Scope
- No remote MCP gateway.
- No custom transport beyond existing stdio baseline.
- No new approval bypass.

## AI-First Planner Design
- MCP is the primary upper-agent integration surface; tools must be discoverable through `tools/list`.
- `job.list` and `job.describe` let the upper agent choose valid jobs before invoking `job.run`.
- `job.run` should return structuredContent with the same evidence as CLI/HTTP.

## Acceptance Criteria
- MCP `tools/list` includes `job.list`, `job.describe`, and `job.run`.
- MCP job discovery returns executable templates.
- MCP `job.run` executes `readiness_check` and returns DONE evidence in smoke tests.

## Risks
- MCP tests spawn a subprocess and can be slower/flakier than in-process tests.
- Stdio transport remains local-only; remote MCP remains future boundary.

## Test Plan
- Extend `tests.test_mcp_server_smoke`.
- Run QA venv `python3 -m unittest tests.test_mcp_server_smoke`.
- Run Stage 12 cycle.
