# Implement Notes

## Changed Files
- `app/cli.py`: added `readiness_check` executable adapter, readiness note rendering, and shared Stage 12 job metadata helper.
- `tests/test_stage12_job_invocation_smoke.py`: added readiness runtime smoke coverage.
- `scripts/run_stage12_local_job_poc.sh`: now runs and validates both `daily_status_digest` and `readiness_check`.
- `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`: documented the second executable job path.

## Rollback Plan
- Remove `readiness_check` from `IMPLEMENTED_JOB_TEMPLATE_IDS`.
- Remove the readiness branch from `_job_runtime_metadata`.
- Remove readiness assertions from smoke tests and the PoC script.
- Revert docs that claim `readiness_check` is executable.

## Known Risks
- The adapter summarizes readiness evidence but does not execute external sandbox/live probes.
- Stage 8 live readiness remains blocked until external env values are supplied.
