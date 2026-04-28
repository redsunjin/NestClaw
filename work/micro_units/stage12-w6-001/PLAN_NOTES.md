# Plan Notes

## Scope
- Add a non-interactive scheduler wrapper around `newclaw job run`.
- Preserve Stage 12's existing job/template/profile/capability validation path.
- Store scheduler evidence in ignored report directories.
- Add cron, launchd, and GitHub Actions examples.

## Out of Scope
- Built-in persistent scheduler service.
- New queue database or retry daemon.
- Human TUI.
- Direct lower-level task/incident scheduler calls.

## AI-First Planner Design
- Upper agents and external schedulers should call a bounded job contract, not raw task or incident internals.
- The wrapper mirrors the expected upper-agent sequence: discover a job, run it, then confirm history evidence.
- The result is intentionally machine-readable so local LLM wrappers can consume `summary.json` without scraping console text.

## Acceptance Criteria
- Wrapper calls `app.cli job run`.
- Wrapper calls `app.cli job history`.
- Wrapper verifies expected status and confirms history contains the task.
- Scheduler smoke runs in the Stage 12 dev-QA cycle.
- Roadmap and manifest identify external schedulers as invocation surfaces, not runtime owners.

## Risks
- If examples call lower-level surfaces, they can bypass job guardrails.
- If evidence is not copied to a deterministic report directory, scheduled jobs become hard to audit.
- If a built-in scheduler is added too early, product scope drifts away from job control plane.

## Test Plan
- Run Stage 12 static contract tests.
- Run Stage 12 runtime job invocation smoke tests.
- Run scheduler smoke through the QA venv runtime.
- Run Stage 12 dev-QA cycle.
