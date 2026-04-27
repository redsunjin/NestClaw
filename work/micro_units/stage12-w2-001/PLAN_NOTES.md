# Plan Notes

## Scope
- Add `newclaw job list` for upper agents and operators to discover runnable and planned job templates.
- Add `newclaw job describe --template <id>` with compatible profiles, capability packs, runtime surfaces, and invocation examples.
- Keep discovery read-only and registry-backed; no runtime task is created by discovery commands.
- Cover the new surfaces with Stage 12 contract tests.

## Out of Scope
- No dashboard redesign.
- No remote marketplace or dynamic plugin discovery.
- No profile or pack mutation through discovery commands.

## AI-First Planner Design
- Discovery output must be deterministic JSON so Claude, Codex, MCP wrappers, schedulers, or local agents can decide which job to run before calling `job run`.
- The payload should expose compatibility and execution status without requiring freeform context.
- Human-readable output is secondary and should summarize only the important job/profile/pack facts.

## Acceptance Criteria
- `newclaw job list --json` returns all enabled job templates with executable status and compatible profile ids.
- `newclaw job describe --template daily_status_digest --json` returns required packs and invocation examples.
- Optional profile filtering shows whether a profile is compatible with a template.
- Contract tests assert CLI parser and documentation references.

## Risks
- Discovery can drift from runtime validation if it duplicates too much logic.
- Too much detail can make upper-agent payloads noisy; keep a compact summary plus registry references.

## Test Plan
- Run `python3 -m unittest tests.test_stage12_contract`.
- Run direct CLI JSON smoke for `job list` and `job describe`.
- Re-run Stage 12 cycle after the readiness adapter is added.
