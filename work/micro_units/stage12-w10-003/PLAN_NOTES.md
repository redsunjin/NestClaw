# Plan Notes

## Scope
Remove production harness warning sources and make Stage 12 QA fail on validator warnings through `--strict-warnings`.

## Out of Scope
Do not implement future jobs such as spec review or profile design review in this unit. Future jobs remain roadmap candidates, not production allowlist entries.

## AI-First Planner Design
Upper agents need a clean machine-readable harness contract. Warnings in production allowlists create ambiguity, so the final Stage 12 line should be warning-free.

## Acceptance Criteria
`python3 scripts/validate_stage12_llm_harness.py --strict-warnings` returns PASS with `warnings=0`, and Stage 12 dev-QA cycle invokes the validator with `--strict-warnings`.

## Risks
Removing placeholder references could hide future intent. The roadmap and candidate docs remain the correct place for future intent; production registries should contain only executable contracts.

## Test Plan
Run strict validator, Stage 12 contract tests, Stage 12 job invocation smoke tests, Stage 12 dev-QA cycle, micro gates, and `git diff --check`.
