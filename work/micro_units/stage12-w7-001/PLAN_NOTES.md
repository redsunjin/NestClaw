# Plan Notes

## Scope
- Add `idempotency_key` and `input_fingerprint` to Stage 12 job invocation metadata.
- Surface those fields through `job.history`.
- Extend the scheduler wrapper with `run`, `skip`, and `fail` duplicate policies.
- Add a scheduler dedupe smoke script.

## Out of Scope
- Global distributed locks.
- A built-in persistent scheduler daemon.
- Cross-actor duplicate suppression.
- Automatic deletion or replay of previous runs.

## AI-First Planner Design
- Upper agents need deterministic run identity so they can tell whether a scheduled request already executed.
- The idempotency key is attached to the job contract, not hidden in shell-only state.
- The wrapper uses history as the source of truth so CLI, HTTP, MCP, and dashboard evidence stay aligned.

## Acceptance Criteria
- `job.run` returns `idempotency_key` and `input_fingerprint`.
- `job.history` includes the same fields.
- `scripts/run_stage12_scheduled_job.sh` supports `--idempotency-key` and `--duplicate-policy`.
- `scripts/run_stage12_scheduler_dedupe_smoke.sh` proves duplicate `skip` behavior.
- Stage 12 dev-QA cycle includes dedupe smoke coverage.

## Risks
- Default dedupe based only on input fingerprint can be too broad for long-running periodic checks.
- `skip` policy must still write evidence so operators can tell why no new job ran.
- Duplicate detection is scoped to visible history for the current actor.

## Test Plan
- Compile changed Python modules.
- Run Stage 12 static contract tests.
- Run Stage 12 job invocation smoke tests.
- Run scheduler smoke and scheduler dedupe smoke.
- Run Stage 12 dev-QA cycle.
