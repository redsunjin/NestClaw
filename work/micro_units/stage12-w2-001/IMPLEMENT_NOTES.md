# Implement Notes

## Changed Files
- `app/cli.py`: added `job list` and `job describe` parser paths, discovery payload helpers, compact human-readable output, and compatibility metadata.
- `tests/test_stage12_job_invocation_smoke.py`: added discovery smoke coverage for executable and planned templates.
- `tests/test_stage12_contract.py`: added static coverage for discovery parser strings, docs, and follow-up campaign.
- `scripts/run_stage12_local_job_poc.sh`: added discovery JSON checks before invocation.
- `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`, `README.md`: documented discovery surfaces.

## Rollback Plan
- Remove `job list` and `job describe` subcommands and discovery helpers from `app/cli.py`.
- Remove discovery assertions from Stage 12 tests and PoC script.
- Revert discovery references in Stage 12 docs.

## Known Risks
- Discovery is currently CLI-only; MCP/HTTP mirrors are still future work.
- Discovery compatibility must continue to share validation assumptions with `job run` to avoid drift.
