# Implement Notes

## Changed Files
- `app/stage12_jobs.py`: extracted shared Stage 12 job contract, discovery, submit payload, and evidence helpers.
- `app/main.py`: added `GET /api/v1/jobs`, `GET /api/v1/jobs/{template_id}`, and `POST /api/v1/jobs/run`.
- `tests/test_stage12_job_invocation_smoke.py`: added HTTP discovery and readiness job run coverage.
- `tests/test_stage12_contract.py`: added HTTP route and campaign coverage.
- `NESTCLAW_AGENT_INTEGRATION_SPEC.md`, `NESTCLAW_INTEGRATION_EXAMPLES.md`, `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`, `README.md`: documented HTTP job surfaces.

## Rollback Plan
- Remove the `/api/v1/jobs*` endpoints and `JobRunRequest` model from `app/main.py`.
- Remove HTTP smoke assertions and route contract assertions.
- Revert HTTP references in integration docs and manifest.

## Known Risks
- `POST /api/v1/jobs/run` intentionally uses sync execution to match CLI/MCP evidence behavior; very long jobs may need async mode later.
- External Stage 8 readiness remains env-gated and is not solved by the HTTP job API.
