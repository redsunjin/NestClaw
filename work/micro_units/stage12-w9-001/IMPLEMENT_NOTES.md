# Implement Notes

## Changed Files
- `scripts/validate_stage12_llm_harness.py`
- `scripts/run_dev_qa_cycle.sh`
- `tests/test_stage12_contract.py`
- `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md`
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`
- `NESTCLAW_CAPABILITY_MANIFEST.md`
- `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`
- `README.md`
- `work/priority_campaigns/stage12-llm-harness-validator-campaign/campaign.json`
- `work/micro_units/stage12-w9-001/`

## Rollback Plan
- Remove the validator script.
- Remove the Stage 12 cycle validator line.
- Remove validator references from docs and contract tests.
- Remove the validator campaign and MWU.

## Known Risks
- The YAML parser is intentionally limited to the current model registry shape.
- Warnings are not failures unless `--strict-warnings` is used.
- Optional/future registry references remain visible as warnings.
