# Review Notes

## Security / Policy Review
- MCP tools require explicit actor id and role fields where runtime access matters.
- Job run goes through the existing orchestration service and cannot bypass policy gates.
- Discovery remains read-only and registry-backed.

## Architecture / Workflow Review
- MCP tools should call the same helper as HTTP and CLI.
- Tool names should use a new `job.*` namespace to keep them distinct from generic `agent.*` runtime surfaces.

## QA Gate Review
- `tools/list` expected tool set must be updated.
- A smoke call to `job.run` should verify completed evidence.

## Review Verdict
- Approved because it is the natural upper-agent surface for Stage 12 job control.
