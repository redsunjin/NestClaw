# Implement Notes

## Changed Files
- `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`: defined the Stage 12 Job Template vocabulary, required fields, input schema rules, provider policy, schedule trigger, output evidence, and runtime invariants.
- `configs/job_templates.json`: added `daily_status_digest`, `issue_triage`, and `readiness_check` sample templates.
- `configs/agent_profiles.json`: updated profile `allowed_job_templates` so sample templates can reference real Agent Profiles.
- `tests/test_stage12_contract.py`: added Job Template contract tests for registry shape, profile references, local-first policy, cloud/API optionality, schedule trigger, and output evidence.
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`, `README.md`: linked the Job Template baseline artifacts.
- `work/priority_campaigns/stage12-priority-campaign/campaign.json`: moved G2 to `in_progress`.
- `work/micro_units/stage12-w1-002/*`: initialized and advanced the G2 micro work unit.

## Rollback Plan
- Revert `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md` and `configs/job_templates.json`.
- Revert the `configs/agent_profiles.json` additions for `issue_triage` if the Job Template vocabulary changes.
- Revert the Stage12 contract test additions for job templates.
- Reset `g2-job-template-spec` in the campaign to `pending` and remove `stage12-w1-002` if G2 is paused.

## Known Risks
- Capability pack ids are referenced before the G3 Capability Pack spec exists; G3 must make those references canonical.
- `configs/job_templates.json` is currently a contract registry, not runtime-enforced validation.
- `newclaw job run` is documented as a planned surface and is not implemented in G2.
