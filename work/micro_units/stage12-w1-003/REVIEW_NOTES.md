# Review Notes

## Security / Policy Review
- Capability Pack must be an allowlist, not a discovery surface.
- Wildcard tool ids are forbidden.
- A pack cannot lower approval requirements from the underlying tool, profile, or job template policy.
- External-system tools must declare data boundary and approval requirements explicitly.
- Packs that include write-capable tools such as Redmine updates or Slack sends must require approver-level approval or dry-run-only handling.
- Cloud/API profiles may use only packs with redacted/public/low data boundaries.

## Architecture / Workflow Review
- Capability Pack binds G1 Agent Profiles and G2 Job Templates to the existing `configs/tool_registry.yaml`.
- The registry should stay JSON and data-only for G3.
- Runtime enforcement should be added in G4 or a later validator once invocation payloads are stable.
- Every pack should expose `allowed_tool_ids`, `denied_tool_ids`, `approval_requirements`, `data_boundary`, `allowed_profile_ids`, and `allowed_template_ids`.
- Contract tests should validate that all referenced tools exist in the current tool registry and that every profile/template pack reference resolves.

## QA Gate Review
- Add Stage12 contract tests for `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md` and `configs/capability_packs.json`.
- Validate JSON shape.
- Validate pack ids against Agent Profile and Job Template references.
- Validate tool ids against `load_tool_registry()`.
- Run Stage8-12 contract tests and bounded Stage12 dev/QA cycle.

## Review Verdict
- Approved for implementation.
- Keep scope limited to spec, registry, cross-reference tests, and work-unit evidence.
- Do not implement runtime pack enforcement or new tools in G3.
