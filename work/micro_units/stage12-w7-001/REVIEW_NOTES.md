# Review Notes

## Security / Policy Review
- Idempotency keys are audit metadata and do not grant permissions.
- Duplicate detection respects the actor visibility rules already enforced by `job.history`.
- The wrapper does not bypass template/profile/capability/budget checks.

## Architecture / Workflow Review
- The runtime records a stable `input_fingerprint` using canonical JSON and SHA-256.
- The scheduler wrapper performs preflight history lookup only when duplicate policy is `skip` or `fail`.
- The default `run` policy preserves backwards compatibility for repeated manual smoke runs.

## QA Gate Review
- Unit smoke must confirm CLI/HTTP job runs preserve idempotency evidence.
- Wrapper smoke must prove a second run with the same key can be skipped.
- Stage 12 cycle must include the dedupe smoke script.

## Review Verdict
- Approved as a bounded scheduler reliability increment. A future distributed lock can be considered only if external schedulers need concurrent execution control.
