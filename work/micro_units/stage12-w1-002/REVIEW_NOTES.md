# Review Notes

## Security / Policy Review
- Job Template must not grant raw tool registry access. It may only reference curated capability pack ids.
- Sensitive or internal templates must default to local provider classes or profiles that deny external send.
- Cloud/API provider classes may appear only through explicit `provider_policy` and must require approval or redaction for external payload transfer.
- Template input schema must describe sensitivity expectations and required fields so upper agents cannot smuggle arbitrary context through free-form payloads.
- Schedule triggers must call NestClaw surfaces and must not bypass approval, status, events, report, or audit evidence.

## Architecture / Workflow Review
- Job Template is the contract between Agent Profile and future runtime invocation.
- The registry should remain data-only JSON for now; runtime validation can be added after Capability Pack schema stabilizes.
- Every template should declare `workflow_family`, `submit_surface`, `status_surface`, `event_surface`, and `report_surface` to preserve the existing runtime model.
- Template budget fields should be local overrides or references, not a separate policy engine yet.
- Job Template samples should use profile ids from `configs/agent_profiles.json` so G1 and G2 vocabularies stay connected.

## QA Gate Review
- Add Stage12 contract tests for the Job Template spec and sample registry.
- Validate JSON shape and profile id references.
- Run Stage8-12 contract tests after adding G2 coverage.
- Run bounded Stage12 dev/QA cycle with `NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15` to prevent optional browser checks from blocking progress.

## Review Verdict
- Approved for implementation.
- Keep this as a bounded spec/registry/contract-test change.
- Do not implement scheduler runtime or local LLM PoC in G2; those belong to later Stage12 items.
