# Review Notes

## Security / Policy Review
- HTTP endpoints require existing actor auth dependency.
- Runtime submission still goes through `ORCHESTRATION_SERVICE.submit_agent`, so requester ownership and role checks remain enforced.
- Discovery exposes committed registry metadata only and no secrets.

## Architecture / Workflow Review
- Extract reusable Stage 12 job contract helpers to avoid CLI/HTTP drift.
- HTTP is a thin adapter over the same job contract and canonical agent runtime surfaces.

## QA Gate Review
- Contract tests should assert HTTP route declarations.
- Runtime smoke should cover discovery and `readiness_check` run.

## Review Verdict
- Approved because it turns existing CLI-only job control into a service surface for upper agents without adding new execution semantics.
