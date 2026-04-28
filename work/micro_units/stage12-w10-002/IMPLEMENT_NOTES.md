# Implement Notes

## Changed Files
- `configs/job_templates.json`
- `scripts/validate_stage12_llm_harness.py`
- `tests/test_stage12_contract.py`
- `scripts/run_stage12_scheduler_smoke.sh`
- `scripts/run_stage12_scheduler_dedupe_smoke.sh`
- `examples/stage12_scheduler/`
- `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
- `NESTCLAW_STAGE12_SCHEDULER_INVOCATION_GUIDE_2026-04-28.md`
- `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md`
- `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`
- `NESTCLAW_CAPABILITY_MANIFEST.md`
- `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`
- `work/priority_campaigns/stage12-job-idempotency-examples-campaign/campaign.json`
- `work/micro_units/stage12-w10-002/`

## Rollback Plan
Remove `idempotency_key_policy` fields, remove validator enforcement, restore scheduler examples to derived-key behavior, and remove the campaign/work-group references.

## Known Risks
The launchd example uses shell interpolation for a daily key bucket, so operators must review the command string before installing it as a real local agent.
