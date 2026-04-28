# Plan Notes

## Scope
- Make `issue_triage` executable through the same shared Stage 12 job contract used by CLI, HTTP, and MCP.
- Map `issue_triage` to the existing incident runtime in dry-run mode so ticket draft governance and approval semantics remain canonical.
- Enforce budget guardrails before runtime submission by rejecting input-level budget overrides, oversized context payloads, and timeout values beyond the selected execution budget.

## Out of Scope
- Live Redmine writes, Slack sends, or any external system mutation.
- A separate chat or TUI runtime.
- Cloud/API provider execution for sensitive internal issue payloads.

## AI-First Planner Design
- Upper agents should discover `issue_triage` through `job.list`, inspect it through `job.describe`, and call `job.run` with a bounded input object.
- The local-first profile remains the default route for internal issue triage.
- The incident planner may use LLM planning only when existing runtime policy enables it; otherwise deterministic fallback remains visible in provenance.

## Acceptance Criteria
- `issue_triage` appears as executable in job discovery.
- `issue_triage` runs as an incident dry-run and captures status, events, report, bundle, and handoff evidence.
- Budget override attempts fail before submission.
- `timeout_seconds` above `max_elapsed_seconds` fails before submission.
- Stage 12 smoke tests cover the new adapter and budget guardrails.

## Risks
- Accidentally treating issue triage as live ticket mutation would weaken Stage 12 safety.
- Duplicating runtime paths outside the incident service would fragment audit and approval evidence.
- Budget fields that are only documented but not enforced would leave local LLM control mostly cosmetic.

## Test Plan
- Compile changed Python modules.
- Run `tests.test_stage12_contract`.
- Run `tests.test_stage12_job_invocation_smoke`.
- Run `tests.test_mcp_server_smoke`.
- Run `bash scripts/run_stage12_local_job_poc.sh`.
