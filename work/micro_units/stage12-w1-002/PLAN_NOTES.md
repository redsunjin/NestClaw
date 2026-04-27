# Plan Notes

## Scope
- Define the canonical Job Template spec for Stage 12 local-first LLM job control.
- Capture repeatable work as a bounded contract with input schema, provider policy, capability pack binding, execution budget reference, schedule trigger, and output evidence.
- Add a machine-readable sample registry with at least three jobs:
  - `daily_status_digest`
  - `issue_triage`
  - `readiness_check`
- Connect job templates to existing `agent.submit/status/events/report` surfaces instead of creating a separate scheduler runtime.
- Add Stage12 contract tests that validate the spec, sample registry, and relation to Agent Profiles.

## Out of Scope
- Implementing a full scheduler.
- Implementing the local LLM execution PoC.
- Creating a natural-language chat interface.
- Defining full Capability Pack schema beyond references required by job templates.
- Allowing arbitrary tool access or arbitrary prompt/task execution.

## AI-First Planner Design
- Job Template constrains the planning problem before an LLM sees the work.
- The template decides which inputs are allowed, which provider classes can be used, which capability packs are visible, and which evidence must be emitted.
- Local LLMs should receive a compact task contract rather than broad project context.
- Cloud/API providers remain optional but must pass through `provider_policy`, sensitivity constraints, and approval rules.
- Upper agents may recommend or submit a job template run, but they should not bypass the NestClaw execution/audit contract.

## Acceptance Criteria
- `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md` exists.
- `configs/job_templates.json` exists with at least three sample jobs.
- Each sample job includes input schema, allowed profile ids, required capability packs, provider policy, schedule trigger, execution budget override, and output evidence.
- Stage12 contract tests validate job template structure and profile references.
- Existing Stage8-12 contract tests still pass.

## Risks
- If job templates are too flexible, they recreate the original general-purpose agent problem.
- If schedule triggers bypass `agent.submit/status/events/report`, audit and approval evidence will fragment.
- If provider policy is vague, cloud/API use can weaken local-first positioning.
- If capability pack references are not validated later, templates may drift into documentation-only contracts.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage12-w1-002`
- `python3 -m unittest tests.test_stage12_contract`
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`
- `env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`
