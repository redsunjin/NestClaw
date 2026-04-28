# Plan Notes

## Scope
Add explicit `idempotency_key_policy` metadata for every implemented Stage 12 job template, update scheduler examples to pass concrete `stage12:` keys, and enforce the policy through the Stage 12 validator and contract tests.

## Out of Scope
Do not add a built-in scheduler, distributed lock, or new persistence layer. The work remains external-scheduler guidance plus job-run/history evidence.

## AI-First Planner Design
Upper agents and local automation should not infer dedupe keys from prose. The planner-facing contract needs copyable key formats, concrete examples, and duplicate policy so Claude/Codex/cron/CI callers invoke NestClaw consistently.

## Acceptance Criteria
Each implemented template has an idempotency key format, concrete example, recommended duplicate policy, and rerun guidance. The validator rejects scheduled jobs missing this policy. Scheduler examples use explicit `stage12:` keys.

## Risks
Overly broad keys can suppress legitimate reruns, while overly narrow keys can allow duplicate work. The chosen formats use business run buckets and deliberately omit `profile_id` so dedupe survives approved routing changes.

## Test Plan
Run the direct validator, Stage 12 contract tests, Stage 12 job invocation smoke tests, scheduler smoke, scheduler dedupe smoke, Stage 12 dev-QA cycle, micro gates, and `git diff --check`.
