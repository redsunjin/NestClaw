# Plan Notes

## Scope
- Add a non-interactive `newclaw job run` CLI surface for one constrained Stage 12 job invocation.
- Resolve `Job Template`, `Agent Profile`, and `Capability Pack` registries before submission.
- Reuse existing `agent.submit`, `agent.status`, `agent.events`, `agent.report`, `agent.bundle`, and `agent.handoff` runtime surfaces instead of creating a separate scheduler or TUI.
- Capture job-level audit fields in the CLI response so upper agents and operators can see the selected template, profile, provider policy, capability packs, task id, report path, events, bundle, and handoff packet.

## Out of Scope
- No standalone human TUI.
- No new background scheduler daemon.
- No live external provider integration or network-dependent local model server requirement.
- No broad support for every future job type; the PoC proves the invocation contract with `daily_status_digest` and leaves room for later templates.

## AI-First Planner Design
- The CLI accepts structured JSON input and produces machine-readable JSON output suitable for Claude, Codex, MCP wrappers, cron, launchd, or other upper agents.
- The job runner validates bounded capability and data boundaries before calling the existing orchestration layer.
- The runtime remains observable through current dashboard/API primitives, preserving NestClaw as an orchestration backend plus human audit dashboard.

## Acceptance Criteria
- `newclaw job run --template daily_status_digest --profile local_ops_default --input-json ... --json` creates and runs a task.
- The response contains `job_invocation`, final `status`, `events`, `report`, and optional `bundle` and `handoff` evidence.
- Invalid template/profile/pack/input combinations fail before runtime submission with a clear error payload.
- Stage 12 contract and smoke tests cover the new invocation path.

## Risks
- Mapping a Stage 12 job into the existing `meeting_summary` runtime is a bridge, not the final job engine.
- Existing runtime dependencies may be unavailable outside the project virtual environment, so smoke tests should skip cleanly when the FastAPI stack is missing.
- Local model availability is intentionally not required; provider fallback evidence must remain visible.

## Test Plan
- Run `python3 -m unittest tests.test_stage12_contract tests.test_stage12_job_invocation_smoke`.
- Run `env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`.
- Run micro-cycle gates for `stage12-w1-004`.
