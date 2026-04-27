# Implement Notes

## Changed Files
- `app/cli.py`: added `job run` command, Stage 12 registry preflight, `daily_status_digest` runtime adapter, and job invocation evidence payload.
- `tests/test_stage12_job_invocation_smoke.py`: added runtime smoke coverage for successful daily status digest invocation and disallowed profile rejection.
- `scripts/run_stage12_local_job_poc.sh`: added reproducible CLI PoC runner.
- `scripts/run_dev_qa_cycle.sh`: added Stage 12 local job smoke and PoC script checks.
- `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`: documented the G4 invocation contract and verification path.
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `README.md`: linked G4 PoC status and surfaces.
- `tests/test_stage12_contract.py`: added static contract coverage for the new CLI, docs, cycle checks, and campaign state.
- `work/priority_campaigns/stage12-priority-campaign/campaign.json`: moved G4 to in-progress during implementation.

## Rollback Plan
- Remove the `job` subcommand and helper functions from `app/cli.py`.
- Remove `tests/test_stage12_job_invocation_smoke.py` and the Stage 12 smoke/script checks from `scripts/run_dev_qa_cycle.sh`.
- Remove `scripts/run_stage12_local_job_poc.sh` and `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`.
- Revert the Stage 12 roadmap/manifest/README references and set G4 back to pending if the runtime path is rejected.

## Known Risks
- `daily_status_digest` currently bridges into the existing `meeting_summary` runtime; future job families still need native adapters.
- Runtime smoke coverage depends on the FastAPI stack, so the plain Python environment may skip it while the QA venv executes it.
- Local model availability is not required for this PoC; provider fallback evidence remains acceptable until a real local model env is supplied.
