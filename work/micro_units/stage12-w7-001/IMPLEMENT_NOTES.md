# Implement Notes

## Changed Files
- `app/stage12_jobs.py`
- `app/cli.py`
- `app/main.py`
- `app/mcp_server.py`
- `app/services/orchestration_service.py`
- `scripts/run_stage12_scheduled_job.sh`
- `scripts/run_stage12_scheduler_dedupe_smoke.sh`
- `scripts/run_dev_qa_cycle.sh`
- `tests/test_stage12_contract.py`
- `tests/test_stage12_job_invocation_smoke.py`
- `NESTCLAW_STAGE12_SCHEDULER_INVOCATION_GUIDE_2026-04-28.md`
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`
- `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`
- `NESTCLAW_CAPABILITY_MANIFEST.md`
- `README.md`
- `work/priority_campaigns/stage12-scheduler-dedupe-campaign/campaign.json`
- `work/micro_units/stage12-w7-001/`

## Rollback Plan
- Remove `idempotency_key` propagation from job surfaces.
- Remove duplicate policy handling from the scheduler wrapper.
- Remove dedupe smoke from Stage 12 cycle.
- Remove docs and contract assertions for scheduler dedupe.

## Known Risks
- Duplicate detection is history-based, so it is not a distributed lock.
- Actors only detect duplicates visible to their role and `requested_by` scope.
- Callers should supply explicit keys for business schedules rather than relying only on input fingerprint defaults.
