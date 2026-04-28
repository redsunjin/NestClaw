# Implement Notes

## Changed Files
- `tests/fixtures/stage12_llm_harness_negative/agent_profiles.json`
- `tests/fixtures/stage12_llm_harness_negative/job_templates.json`
- `tests/fixtures/stage12_llm_harness_negative/capability_packs.json`
- `tests/fixtures/stage12_llm_harness_negative/model_registry.yaml`
- `tests/test_stage12_contract.py`
- `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md`
- `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`
- `work/priority_campaigns/stage12-llm-harness-negative-fixtures-campaign/campaign.json`
- `work/micro_units/stage12-w10-001/`

## Rollback Plan
Remove the negative fixture directory, remove the new Stage 12 contract tests, and remove the campaign/work-group references.

## Known Risks
The test checks representative errors rather than a full exact error list, so a validator change could still alter non-asserted diagnostics. The lower-bound error count reduces that risk without making the fixture noisy.
