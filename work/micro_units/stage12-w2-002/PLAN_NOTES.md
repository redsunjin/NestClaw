# Plan Notes

## Scope
- Add executable adapter support for `readiness_check`.
- Reuse existing `meeting_summary` runtime as the bridge until native job engines exist.
- Capture status, events, report, bundle, and handoff evidence through the existing job invocation path.
- Add smoke coverage for the readiness job.

## Out of Scope
- No Stage 8 sandbox/live env provisioning.
- No actual external readiness execution beyond summarizing bounded readiness input.
- No new scheduler daemon.

## AI-First Planner Design
- `readiness_check` should be callable by upper agents as a bounded local-first job with structured input.
- The adapter should make check set, target stage, env profile, strict gate, timeout, and sensitivity visible in the generated report notes.
- Runtime evidence should stay identical to `daily_status_digest` so agents can consume both jobs through one response shape.

## Acceptance Criteria
- `newclaw job run --template readiness_check --profile local_ops_default --json` completes in QA runtime.
- Response includes `readiness_probe_readonly` and `core_status_readonly` packs.
- Smoke tests assert DONE status, event evidence, report file, bundle, and handoff.

## Risks
- This is still a summary adapter, not a true readiness executor.
- Stage 8 live readiness remains blocked by external env and must not be represented as solved.

## Test Plan
- Run `env PATH=/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH python3 -m unittest tests.test_stage12_job_invocation_smoke`.
- Run `env PATH=/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`.
