# Review Notes

## Security / Policy Review
- Scheduler calls retain actor context with `--actor-id` and `--actor-role`.
- The wrapper does not expand budgets or override profile/template/pack policy.
- Evidence files are local reports and do not trigger external sends.

## Architecture / Workflow Review
- External scheduling is appropriate for small organizations because cron, launchd, and CI already solve timing.
- NestClaw should own execution contracts and evidence, not calendar semantics.
- The wrapper keeps the runtime path on `job.run` and `job.history`, so it does not create a parallel scheduler-specific execution model.

## QA Gate Review
- Static contract tests should assert wrapper and examples exist.
- Runtime smoke should execute `readiness_check` through the wrapper.
- Stage 12 cycle should include the scheduler smoke as optional runtime coverage.

## Review Verdict
- Approved with the boundary that scheduler examples must call the Stage 12 job surface only.
