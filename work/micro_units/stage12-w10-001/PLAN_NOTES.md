# Plan Notes

## Scope
Add Stage 12 LLM harness negative fixtures that intentionally violate local/cloud provider boundaries, sensitivity policy, mutual job/profile/pack allowlists, scheduled idempotency requirements, capability-pack policy, and model routing references.

## Out of Scope
Do not change the production registry policy and do not introduce a new runtime provider. This unit only hardens validator evidence.

## AI-First Planner Design
Upper agents and local LLM operators need executable policy evidence, not only prose. The negative fixtures make the validator contract clear to future agent-driven config edits by proving which unsafe changes must fail before runtime.

## Acceptance Criteria
The repository contains a dedicated negative fixture directory. Stage 12 contract tests invoke `scripts/validate_stage12_llm_harness.py --json` against the fixture and assert a non-zero exit with a `FAIL` payload and representative policy errors.

## Risks
The fixture could become too brittle if it asserts every generated error. The test therefore checks representative errors across policy classes and a lower-bound error count.

## Test Plan
Run the direct validator on the production config, run `python3 -m unittest tests.test_stage12_contract`, run Stage 12 job invocation smoke tests, and run `bash scripts/run_dev_qa_cycle.sh 12`.
