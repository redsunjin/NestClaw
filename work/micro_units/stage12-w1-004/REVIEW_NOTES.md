# Review Notes

## Security / Policy Review
- The PoC validates the selected profile and required packs before submission.
- `daily_status_digest` remains local-first with `external_send_policy: deny` and the `internal_digest_basic` pack blocks tool writes and external send.
- Actor role validation continues to use existing CLI `ActorContext` and orchestration authorization.

## Architecture / Workflow Review
- The new surface is a thin job-contract adapter over existing agent runtime surfaces.
- Runtime evidence remains canonical in task status, events, report, bundle, and handoff; the job wrapper only adds Stage 12 selection context.
- This keeps NestClaw positioned as a job control plane for upper agents rather than a second UI/runtime stack.

## QA Gate Review
- Contract tests must assert that the CLI, Stage 12 docs, and cycle script include the job invocation path.
- Smoke tests must execute one local-first job and assert DONE status, event capture, report file creation, bundle capture, and completed handoff packet.
- Dependency-gated smoke tests should skip when runtime imports are unavailable rather than making static checks brittle.

## Review Verdict
- Approved for implementation as a bounded PoC because it reuses existing runtime behavior, avoids external dependencies, and produces operator/agent-readable evidence.
