# Plan Notes

## Scope
Promote Ollama as a concrete local provider profile, add an onboarding guide, add a smoke script, and wire the smoke into Stage 12 QA.

## Out of Scope
Do not require a live Ollama daemon for default CI/dev QA. The optional live check is gated by `NEWCLAW_STAGE12_OLLAMA_LIVE_CHECK=1`.

## AI-First Planner Design
Local LLM use should be a constrained profile/job/capability contract. The onboarding smoke gives upper agents a non-interactive proof that the profile can run bounded jobs without direct tool sprawl.

## Acceptance Criteria
`local_ollama_ops` resolves to `local_primary`, is `local_llm`, denies external send, is compatible with all implemented Stage 12 templates, and can execute `readiness_check` through `job.run`.

## Risks
The default smoke proves NestClaw routing and evidence, not model quality. Live model availability remains operator-owned.

## Test Plan
Run strict validator, Stage 12 contract tests, local LLM onboarding smoke, Stage 12 job invocation smoke, Stage 12 dev-QA cycle, micro gates, and `git diff --check`.
