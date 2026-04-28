# Plan Notes

## Scope
- Add a Stage 12 LLM harness policy validator.
- Validate model registry, agent profiles, job templates, and capability packs together.
- Wire the validator into `scripts/run_dev_qa_cycle.sh 12`.
- Add contract tests and documentation references.

## Out of Scope
- Mutating registry files automatically.
- Enforcing distributed scheduler locks.
- Adding new LLM providers or job templates.
- Strictly failing on future placeholder jobs currently present in profiles.

## AI-First Planner Design
- Upper agents need machine-checkable harness contracts, not only narrative docs.
- The validator should catch policy regressions before a new local LLM or cloud/API provider is used.
- Warnings are allowed for intentionally future-facing registry references, but policy violations must fail.

## Acceptance Criteria
- `scripts/validate_stage12_llm_harness.py` exists and runs without third-party dependencies.
- The validator checks local/cloud profile boundaries, job/profile/pack allowlists, scheduled idempotency fields, and provider registry references.
- Stage 12 dev-QA cycle runs the validator as a required check.
- Contract tests assert the validator and campaign exist.

## Risks
- Overly strict validation can block intentional future placeholder references.
- Overly weak validation can let local-first policy drift.
- The validator is a preflight gate, not a replacement for runtime smoke tests.

## Test Plan
- Run the validator directly.
- Run Stage 12 static contract tests.
- Run Stage 12 job invocation smoke tests.
- Run Stage 12 dev-QA cycle.
- Run `git diff --check`.
