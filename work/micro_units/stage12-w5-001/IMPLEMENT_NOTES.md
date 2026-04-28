# Implement Notes

## Changed Files
- `app/services/orchestration_service.py`: added Stage 12 job metadata extraction and `job_run_history`.
- `app/main.py`: added `GET /api/v1/jobs/runs`.
- `app/cli.py`: added `newclaw job history`.
- `app/mcp_server.py`: added `job.history`.
- `app/static/agent-console.html`: added read-only Stage 12 job run history panel.
- `app/static/agent-console.js`: added job history loading and rendering.
- `app/static/agent-console.css`: added layout styling for the job run panel.
- Runtime and contract tests updated for the new surface.

## Rollback Plan
- Remove `job.history` from MCP and CLI.
- Remove `GET /api/v1/jobs/runs`.
- Remove dashboard job history panel.
- Leave existing `agent.recent` untouched because it remains the generic fallback.

## Known Risks
- History currently depends on in-process/runtime state persistence already used by the task store.
- Scheduler-specific run grouping is not implemented yet.
