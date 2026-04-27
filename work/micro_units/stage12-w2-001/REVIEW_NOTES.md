# Review Notes

## Security / Policy Review
- Discovery is read-only and does not invoke providers or tools.
- Payloads expose registry metadata already committed in repository configs; no secrets or live env values are returned.
- Profile compatibility should never bypass runtime validation; `job run` remains the enforcing path.

## Architecture / Workflow Review
- Reuse the same registry loaders and compatibility checks used by `job run`.
- Discovery belongs in CLI now because upper agents and scripts need a non-interactive machine-readable surface first.
- A future MCP/HTTP discovery endpoint can mirror the same payload shape.

## QA Gate Review
- Static contract tests must check parser strings and docs.
- Lightweight CLI JSON smoke should verify shape without creating a task.

## Review Verdict
- Approved as the next Stage 12 expansion because it unblocks upper-agent orchestration without expanding runtime risk.
