# Plan Notes

## Scope
- Define the canonical Agent Profile spec for Stage 12 local-first LLM job control.
- Capture local provider, cloud/API provider, upper-agent wrapper, and deterministic fallback in one vocabulary.
- Include allowed job templates, allowed capability packs, execution budget, sensitivity boundary, approval policy, and audit level.
- Add a sample machine-readable profile registry or schema draft if it keeps implementation grounded.
- Connect the spec to model registry, capability manifest, and Stage 12 roadmap.

## Out of Scope
- Implementing full scheduler/runtime job execution.
- Building new dashboard UI.
- Creating an agent marketplace or persona catalog.
- Allowing unrestricted local LLM filesystem/tool access.
- Sending sensitive data to cloud/API providers without explicit policy.

## AI-First Planner Design
- This stage makes local LLM usage predictable by reducing the choice space before planning starts.
- The Agent Profile is not a persona prompt. It is a policy and capability boundary for a provider or wrapper.
- Local providers should be the default for sensitive/internal jobs, while cloud/API providers remain available through explicit provider routing rules.
- Upper agents can design or review profiles, but runtime execution should still go through NestClaw approval/audit contracts.

## Acceptance Criteria
- `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md` or equivalent spec exists.
- The spec defines local LLM, cloud/API LLM, upper-agent, and deterministic fallback profile classes.
- The spec includes execution budget and sensitivity boundary fields.
- At least two sample profiles exist: one local-first profile and one cloud/API-optional profile.
- Existing contract tests for Stage 9-11 still pass.

## Risks
- If profiles are described as agents, the product may drift into agent hub positioning.
- If cloud/API profiles do not carry sensitivity boundaries, local-first becomes weak.
- If execution budget is not part of the profile, local LLM context/tool overuse remains unsolved.
- If profile schema is too detailed before runtime binding exists, it may become paperwork instead of a useful contract.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage12-w1-001`
- `python3 -m unittest tests.test_stage11_contract tests.test_stage10_contract tests.test_stage9_contract`
- If a Stage 12 contract test is added, run `python3 -m unittest tests.test_stage12_contract`
