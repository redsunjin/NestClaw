# Plan Notes

## Scope
Add a read-only Stage 12 harness status endpoint and dashboard panel showing strict validator status, profile/job/pack/provider counts, and local onboarding profile details.

## Out of Scope
Do not add dashboard editing for profiles, jobs, or capability packs. Harness mutation remains file/config governance plus validator gates.

## AI-First Planner Design
Upper agents and operators need to see the same harness state before scheduling or invoking local LLM jobs. The dashboard should read the canonical config state without becoming the source of truth.

## Acceptance Criteria
`GET /api/v1/llm-harness` returns read-only harness state, the console renders an LLM Harness panel, and runtime tests cover the endpoint and static assets.

## Risks
The dashboard can become mistaken for a profile editor. The panel is intentionally read-only and exposes status, not controls.

## Test Plan
Run Stage 12 contract tests, web console runtime tests, Stage 12 job invocation smoke tests, Stage 12 dev-QA cycle, micro gates, and `git diff --check`.
