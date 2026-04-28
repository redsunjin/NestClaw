# Implement Notes

## Changed Files
- `app/stage12_jobs.py`: added `issue_triage` adapter mapping, budget enforcement helpers, and budget evidence in job invocation metadata.
- `app/cli.py`: aligned implemented job template set with the shared Stage 12 contract.
- `scripts/run_stage12_local_job_poc.sh`: added `issue_triage` to the executable PoC path.
- `tests/test_stage12_job_invocation_smoke.py`: added dry-run issue triage and budget rejection coverage.
- `tests/test_mcp_server_smoke.py`: asserted MCP discovery exposes `issue_triage` as executable.
- `tests/test_stage12_contract.py`: added campaign and source-level contract checks.

## Rollback Plan
- Remove `issue_triage` from `IMPLEMENTED_JOB_TEMPLATE_IDS`.
- Remove the `issue_triage` metadata adapter branch in `app/stage12_jobs.py`.
- Keep budget enforcement if possible, because it is a safety improvement independent of the adapter.

## Known Risks
- The incident runtime still uses deterministic fallback unless live planner env is explicitly enabled.
- Live external ticket writes remain out of scope and still require existing approval/live mode controls.
