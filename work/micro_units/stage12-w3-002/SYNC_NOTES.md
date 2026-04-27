# Sync Notes

## Release Actions
- MCP `job.list`, `job.describe`, and `job.run` tools added.
- Capability manifest now marks `job.*` as upper-agent-safe controls.
- `stage12-w3-002` and `stage12-agent-facing-job-api-campaign` marked completed.

## QA Sync Evidence
- Plan gate: `work/micro_units/stage12-w3-002/reports/plan-gate-20260427T162346Z.md`
- Review gate: `work/micro_units/stage12-w3-002/reports/review-gate-20260427T162346Z.md`
- Implement gate: `work/micro_units/stage12-w3-002/reports/implement-gate-20260427T162346Z.md`
- Evaluate gate: `work/micro_units/stage12-w3-002/reports/evaluate-gate-20260427T162455Z.md`
- Stage 12 cycle: `reports/qa/cycle-20260427T162455Z.md`
- Runtime smoke: `tests.test_mcp_server_smoke`

## Final State
- DONE. Upper agents can discover and run Stage 12 jobs over MCP stdio.
