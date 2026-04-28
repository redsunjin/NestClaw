# NestClaw LLM Harness Configuration Guide

## Purpose
NestClaw's LLM harness is not a generic agent playground. It is the configuration boundary that decides which LLM may run which job, with which tools, under which budget and data policy, and how the result is audited.

For the current product direction, harness setup must follow this order:

1. Provider Harness
2. Agent Profile Harness
3. Job Template Harness
4. Capability Pack Harness
5. Invocation Harness
6. QA Harness

The order matters. A new local LLM should not receive tool access until its profile, job templates, capability packs, invocation path, and QA gates are all defined.

## Harness Layers
| Layer | Primary Files | Responsibility |
| --- | --- | --- |
| Provider Harness | `configs/model_registry.yaml` | Register local/cloud/fallback providers and routing metadata. |
| Agent Profile Harness | `configs/agent_profiles.json` | Bind provider class to allowed jobs, capability packs, sensitivity boundary, approval policy, and execution budget. |
| Job Template Harness | `configs/job_templates.json` | Define the repeatable task, input schema, provider policy, schedule trigger, and output evidence. |
| Capability Pack Harness | `configs/capability_packs.json` | Restrict tools and runtime read surfaces with allowlists, denylists, and approval requirements. |
| Invocation Harness | `app/cli.py`, `app/main.py`, `app/mcp_server.py`, `scripts/run_stage12_scheduled_job.sh` | Expose non-interactive CLI, HTTP, MCP, and scheduler-safe job execution. |
| QA Harness | `scripts/run_dev_qa_cycle.sh`, `tests/test_stage12_contract.py`, `tests/test_stage12_job_invocation_smoke.py` | Prove that registry changes and invocation paths do not bypass policy or break runtime evidence. |

The QA harness now includes `scripts/validate_stage12_llm_harness.py`, which checks the machine-readable policy relationships before runtime smoke tests execute. It also includes negative fixtures under `tests/fixtures/stage12_llm_harness_negative/` so validator changes must prove they reject unsafe local/cloud, sensitivity, allowlist, idempotency, and capability-pack configurations.

## Default Profiles
Use the existing profiles as the starting policy set:

- `local_ops_default`: default for internal and sensitive internal work. It is local-first and denies external send.
- `cloud_review_optional`: allowed only for public, low, or redacted metadata where external send is approved.
- `upper_agent_control_readonly`: for Claude/Codex/MCP wrappers that inspect or orchestrate NestClaw without tool writes.
- `deterministic_fallback_default`: for readiness and degraded-mode checks when LLM providers are unavailable.

Do not model these as persona agents. They are execution policy profiles.

## Adding A New Local LLM
Follow this sequence:

1. Add the provider to `configs/model_registry.yaml`.
2. Add or update one profile in `configs/agent_profiles.json`.
3. Keep `provider_class` as `local_llm` unless the provider is a cloud/API or upper-agent wrapper.
4. Set `sensitivity_boundary.external_send_policy` to `deny` for internal local work.
5. Set `execution_budget.allow_network` to `false` unless a separate live integration is approved.
6. Bind only the required job templates in `allowed_job_templates`.
7. Bind only the required capability packs in `allowed_capability_packs`.
8. Add or update a job template if the work is not already represented.
9. Add or update capability packs so tools are allowlisted, not discovered freely by the LLM.
10. Run Stage 12 QA before using the profile in automation.

Minimum validation:

```bash
python3 scripts/validate_stage12_llm_harness.py
python3 -m unittest tests.test_stage12_contract
env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH \
  python3 -m unittest tests.test_stage12_job_invocation_smoke
env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH \
  NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=30 \
  NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 \
  bash scripts/run_dev_qa_cycle.sh 12
```

## Adding A Cloud/API Provider
Cloud/API providers are optional and must not weaken the local-first posture.

Required policy:

- `provider_class`: `cloud_api_llm`
- allowed sensitivity: `public`, `low`, or `redacted_metadata`
- `external_send_policy`: `approval_required`
- `approval_policy.external_send`: `approver_required`
- `redaction_required`: `true`
- no `sensitive_internal` payload by default

Cloud/API LLMs are appropriate for spec review, low-sensitivity summarization, and reasoning over redacted metadata. They are not the default execution path for internal organization data.

## Job Template Rules
Every job template must be a bounded work contract:

- It must define required input fields.
- It must include `sensitivity` or an equivalent sensitivity field.
- `freeform_context_allowed` should stay `false` unless a separate review approves broader context intake.
- It must bind explicit profile IDs.
- It must bind explicit capability pack IDs.
- It must define output evidence through status, events, report, and handoff/bundle surfaces.
- Scheduled jobs must define idempotency key fields or provide an explicit key at invocation time.

If a task cannot be expressed as a job template, it is not ready for local LLM automation.

## Capability Pack Rules
Capability packs are the main defense against local LLM tool sprawl.

Required policy:

- `allowed_tool_ids` must be explicit.
- `denied_tool_ids` must block risky defaults that are not needed.
- `runtime_read_surfaces` must be explicit for readonly packs.
- `tool_write` must be `blocked` or `approver_required`.
- `external_send` must be `blocked` or `approver_required`.
- pack changes require admin review.

Do not give a local LLM direct access to the full tool registry. The LLM should see only the tools attached to the active job's capability packs.

## Invocation Rules
Upper agents, shell scripts, cron, launchd, and CI should invoke jobs through one of the canonical surfaces:

- CLI: `python3 -m app.cli job run ...`
- HTTP: `POST /api/v1/jobs/run`
- MCP: `job.run`
- Scheduler wrapper: `bash scripts/run_stage12_scheduled_job.sh ...`

Do not schedule lower-level task or incident endpoints directly. That bypasses Stage 12 job preflight and makes audit evidence harder to interpret.

For repeated external schedules, use:

```bash
bash scripts/run_stage12_scheduled_job.sh \
  --template readiness_check \
  --profile local_ops_default \
  --input-file examples/stage12_scheduler/readiness-input.json \
  --idempotency-key readiness-stage12-2026-04-28 \
  --duplicate-policy skip
```

## Evidence Requirements
A valid harnessed run must expose:

- `task_id`
- `template_id`
- `profile_id`
- `provider_id`
- `provider_class`
- `capability_pack_ids`
- `execution_budget`
- `budget_enforcement`
- `idempotency_key`
- `input_fingerprint`
- `status`
- `events`
- `report_path`
- optional `agent.bundle`
- optional `agent.handoff`

If the run cannot be explained from `job.run` and `job.history`, the harness is incomplete.

## Anti-Patterns
Avoid these patterns:

- Adding a model provider without a matching profile.
- Letting a local LLM choose from the full tool registry.
- Putting sensitive internal data through a cloud/API profile.
- Treating profiles as named persona agents.
- Scheduling raw task or incident endpoints.
- Expanding execution budget through input payloads.
- Running runtime smoke tests in parallel against the same default SQLite state file.

## Current Recommended Baseline
For small organizations and clubs:

- Use `local_ops_default` for internal repeated work.
- Use `readiness_check` and `daily_status_digest` as the first scheduled jobs.
- Use `issue_triage` only in dry-run until live write approval is explicitly configured.
- Use `cloud_review_optional` only for redacted or low-sensitivity review.
- Use `upper_agent_control_readonly` for Claude/Codex-style orchestration clients.
- Keep the dashboard as approval/audit/status surface, not the main chat product.

## Change Review Checklist
Before merging a harness change, verify:

- Provider class matches local/cloud/fallback intent.
- Sensitivity boundary matches provider class.
- Job templates and profiles are mutually allowlisted.
- Capability packs are mutually bound to profiles and job templates.
- Tool writes and external sends have correct approval policy.
- Budget limits are explicit and cannot be overridden by job input.
- Scheduled jobs have explicit idempotency policy.
- `scripts/validate_stage12_llm_harness.py` returns `PASS`.
- `tests/fixtures/stage12_llm_harness_negative/` still returns `FAIL` through the validator contract test.
- Stage 12 contract tests and runtime smoke tests pass.
