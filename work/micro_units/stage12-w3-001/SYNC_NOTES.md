# Sync Notes

## Release Actions
- Stage 12 HTTP job API added: list, describe, and run.
- Shared `app/stage12_jobs.py` contract helper added for CLI/HTTP/MCP reuse.
- `stage12-w3-001` marked DONE.

## QA Sync Evidence
- Plan gate: `work/micro_units/stage12-w3-001/reports/plan-gate-20260427T162346Z.md`
- Review gate: `work/micro_units/stage12-w3-001/reports/review-gate-20260427T162346Z.md`
- Implement gate: `work/micro_units/stage12-w3-001/reports/implement-gate-20260427T162346Z.md`
- Evaluate gate: `work/micro_units/stage12-w3-001/reports/evaluate-gate-20260427T162408Z.md`
- Stage 12 cycle: `reports/qa/cycle-20260427T162408Z.md`
- Runtime smoke: `tests.test_stage12_job_invocation_smoke`

## Final State
- DONE. Upper agents can call Stage 12 jobs through HTTP without shelling out to CLI.
