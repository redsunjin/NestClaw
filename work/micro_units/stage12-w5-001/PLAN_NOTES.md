# Plan Notes

## Scope
- Add a Stage 12 job run history surface derived from existing runtime task records.
- Expose history through HTTP, CLI, and MCP so upper agents can audit what they invoked.
- Add a read-only job run panel to the operator dashboard without creating a separate chat or runtime path.

## Out of Scope
- Persistent scheduler design.
- Editing or retrying job runs from the dashboard.
- Live external writes or new approval semantics.

## AI-First Planner Design
- Upper agents should call `job.history` after `job.run` to confirm completion, report path, budget evidence, and runtime state.
- Requester role only sees own job runs; reviewer, approver, and admin can inspect broader run history.
- The dashboard mirrors the same HTTP payload rather than inventing a different frontend-only state model.

## Acceptance Criteria
- HTTP exposes `GET /api/v1/jobs/runs`.
- CLI exposes `newclaw job history`.
- MCP exposes `job.history`.
- The web console includes a Stage 12 job run history panel.
- Tests cover history visibility after a job run.

## Risks
- Duplicating task history and job history could drift if they use separate stores.
- Showing too much payload in the dashboard could leak job input data, so the panel should show metadata/evidence rather than raw input.
- Placing `/api/v1/jobs/runs` after `/api/v1/jobs/{template_id}` would cause route ambiguity.

## Test Plan
- Compile changed Python modules.
- Run Stage 12 contract tests.
- Run Stage 12 job invocation smoke tests.
- Run MCP smoke tests.
- Run capability manifest and CLI smoke tests.
- Run web console runtime tests.
- Run Stage 12 dev-QA cycle.
