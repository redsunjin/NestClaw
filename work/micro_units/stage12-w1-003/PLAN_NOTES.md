# Plan Notes

## Scope
- Define the canonical Capability Pack spec for Stage 12 local-first LLM job control.
- Add a machine-readable sample registry that covers all pack ids referenced by `configs/agent_profiles.json` and `configs/job_templates.json`.
- Connect packs to allowed tools, denied tools, approval requirements, data boundary, risk level, allowed profile ids, and allowed job template ids.
- Add contract tests that prove pack ids are curated, reference existing tool registry entries, and are allowed by the profiles/templates that use them.

## Out of Scope
- Implementing runtime enforcement of capability packs.
- Implementing a capability marketplace.
- Adding new live tools to the base tool registry.
- Implementing the local LLM job invocation PoC.
- Changing dashboard UI.

## AI-First Planner Design
- Capability Pack is the tool visibility boundary given to an LLM after profile and template selection.
- A local LLM should receive only the pack-linked tool subset, not the full tool registry.
- Upper agents can propose pack changes through draft/review flows, but runtime use must still be curated and auditable.
- Cloud/API use must not expand tool access; provider class and data boundary must be stricter or equal to profile/template policy.

## Acceptance Criteria
- `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md` exists.
- `configs/capability_packs.json` exists and includes every pack referenced by Agent Profiles and Job Templates.
- Each pack defines allowed tools, denied tools, approval requirements, data boundary, risk level, allowed profiles, and allowed templates.
- Contract tests validate pack references against `configs/tool_registry.yaml`, `configs/agent_profiles.json`, and `configs/job_templates.json`.
- Existing Stage8-12 contract tests still pass.

## Risks
- If packs can use wildcard tools, local LLMs regain broad tool access.
- If pack approval requirements conflict with template/profile policy, the effective permission model becomes unclear.
- If pack ids are not validated, G1/G2 references can drift.
- If G3 tries to enforce runtime behavior before the PoC, it may add brittle code paths.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage12-w1-003`
- `python3 -m unittest tests.test_stage12_contract`
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`
- `env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`
