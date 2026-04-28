# Plan Notes

## Scope
- Add a canonical LLM harness configuration guide.
- Define provider, profile, job template, capability pack, invocation, and QA harness responsibilities.
- Link the guide from Stage 12 roadmap, manifest, work groups, README, and contract tests.

## Out of Scope
- Adding a new provider.
- Changing runtime provider routing.
- Reworking dashboard UI.
- Replacing existing Stage 12 registries.

## AI-First Planner Design
- Upper agents need a clear machine-operable boundary before they can safely ask local LLMs to run work.
- The guide should make clear that profiles are policy harnesses, not persona agents.
- The workflow should discourage unrestricted tool discovery and raw task/incident scheduling.

## Acceptance Criteria
- `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md` exists.
- The guide names the six harness layers and their primary files.
- Docs link the guide from roadmap, manifest, work groups, and README.
- Stage 12 contract tests assert the guide and campaign exist.

## Risks
- If the guide is too broad, future work may interpret NestClaw as an agent marketplace.
- If it is too narrow, local LLM setup will remain tribal knowledge.
- If QA harness constraints are omitted, registry changes may bypass runtime evidence.

## Test Plan
- Run Stage 12 contract tests.
- Run Stage 12 dev-QA cycle.
- Run `git diff --check`.
