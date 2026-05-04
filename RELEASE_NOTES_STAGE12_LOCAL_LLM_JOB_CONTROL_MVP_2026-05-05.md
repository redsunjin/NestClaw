# Release Notes: Stage 12 Local LLM Job Control MVP

- release_date: 2026-05-05
- intended_release_type: internal beta
- recommended_tag: v0.2.0-stage12
- branch: codex/ideation-lab
- release_positioning: local-first LLM job control plane with optional cloud/API provider routing

## Release Judgment
This release is ready for an internal beta. It is not a full external live production release because Stage 8 sandbox/live readiness remains blocked by missing external environment variables.

NestClaw should be used as an orchestration backend and human approval/audit dashboard for bounded LLM jobs, not as a general-purpose free-form chat application.

## Product Scope
Stage 12 fixes the product direction around local-first LLM job control:

- Define repeatable jobs as governed job templates.
- Bind jobs to explicit agent profiles, model providers, and curated capability packs.
- Let local LLMs execute bounded work through the same contracts used by CLI, API, MCP, and scheduler entrypoints.
- Preserve cloud/API LLM optionality behind provider policy, sensitivity boundaries, and approval gates.
- Expose harness health and registry status to the operator dashboard without allowing dashboard-side mutation.

## Completed Stage 12 Work
- Agent profile specification and registry.
- Job template specification and three concrete job templates.
- Curated capability pack binding.
- Local LLM job invocation PoC.
- Scheduler invocation wrapper.
- Scheduled job idempotency and duplicate run/skip/fail policy.
- LLM harness configuration guide.
- Strict LLM harness policy validator.
- Negative validator fixtures for boundary and policy violations.
- Job template idempotency examples.
- Zero-warning production harness validation.
- Local Ollama provider onboarding profile and smoke script.
- Read-only dashboard harness visibility endpoint and console panel.

## Verification Evidence
Fresh local validation:

```text
python3 scripts/validate_stage12_llm_harness.py --strict-warnings
Stage 12 LLM harness validation: PASS
counts: profiles=5 job_templates=3 capability_packs=7 model_providers=3 errors=0 warnings=0
```

Fresh pre-tag dev-QA cycle with a Python 3.12 virtualenv:

```text
reports/qa/cycle-20260504T170812Z.md
pass: 61
fail: 0
skip: 16
```

Most recent broader QA report from the prepared runtime environment:

```text
reports/qa/cycle-20260428T163914Z.md
pass: 72
fail: 0
skip: 5
```

The skipped checks are environment-gated, dependency-gated, or intentionally skipped nested self-evaluation checks. They are not new functional failures.

## Known External Blockers
Stage 8 external readiness remains blocked until these environment variables are provided:

- `NEWCLAW_STAGE8_SANDBOX_ENABLED`
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL`
- `NEWCLAW_STAGE8_SANDBOX_PROJECT`
- `NEWCLAW_STAGE8_LIVE_ENABLED`
- `NEWCLAW_REDMINE_MCP_ENDPOINT`

Once these are available, rerun the readiness bundle from the QA worktree:

```bash
cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa
source .venv/bin/activate
bash scripts/run_stage8_readiness_bundle.sh
```

## Efficient Usage
The recommended operating model is:

1. Define repeated work in `configs/job_templates.json`.
2. Bind model and sensitivity rules in `configs/agent_profiles.json`.
3. Bind allowed tools through `configs/capability_packs.json`.
4. Invoke jobs through CLI, API, MCP, or scheduler wrappers.
5. Review status, approval, run history, and harness health through the operator dashboard.

This is most effective for local LLM operation where context, tools, permissions, repeatability, and auditability need to be constrained.

## Release Boundary
This release is suitable for:

- local-first LLM job execution experiments;
- small organization or club-level internal automation;
- upper-agent orchestration through bounded NestClaw jobs;
- scheduled operational jobs with idempotency and audit history;
- approval-gated dry-run workflows.

This release is not yet suitable for:

- fully open-ended agent marketplaces;
- unmanaged live writes to external systems;
- large multi-tenant SaaS operation;
- external production readiness claims without the Stage 8 env-gated readiness pass.
