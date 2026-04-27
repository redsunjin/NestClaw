# Plan Notes

## Scope
- Add HTTP API endpoints for Stage 12 job discovery and invocation.
- Endpoints must reuse the same registry validation and payload shape as CLI.
- Cover `GET /api/v1/jobs`, `GET /api/v1/jobs/{template_id}`, and `POST /api/v1/jobs/run`.
- Runtime response must include status, events, report, and optional bundle/handoff evidence.

## Out of Scope
- No dashboard UI changes.
- No external scheduler daemon.
- No live readiness env provisioning.

## AI-First Planner Design
- HTTP output must be deterministic JSON for upper agents that cannot or should not shell out to CLI.
- Discovery should show executable status and compatible profile ids before invocation.
- Invocation should remain bounded by template/profile/pack validation.

## Acceptance Criteria
- HTTP job list returns `daily_status_digest`, `readiness_check`, and planned `issue_triage`.
- HTTP job describe returns capability packs and invocation surfaces.
- HTTP job run executes `readiness_check` and returns completed evidence in QA runtime.

## Risks
- HTTP/CLI contract drift if validation is duplicated.
- Actor/requester mismatch should continue to be enforced by the orchestration service.

## Test Plan
- Add runtime smoke tests with FastAPI `TestClient`.
- Run `python3 -m unittest tests.test_stage12_contract`.
- Run QA venv runtime smoke and Stage 12 cycle.
