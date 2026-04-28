# NestClaw Job Template Spec

## Purpose
Job Template is the Stage 12 contract for repeatable LLM-assisted work.

It is not a free-form prompt and it is not a scheduler implementation. It describes what inputs are accepted, which Agent Profiles may run the job, which capability packs are visible, how provider policy is resolved, which schedule triggers may invoke it, and what evidence must be emitted.

## Canonical Registry
- Draft registry: `configs/job_templates.json`
- Status: Stage 12 baseline contract
- Depends on: `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
- Runtime binding: planned after Capability Pack spec and validation are stable

## Required Fields
| Field | Type | Requirement |
| --- | --- | --- |
| `template_id` | string | Stable id used by profiles, CLI, API, MCP, and audit evidence |
| `display_name` | string | Human-readable label for dashboard and handoff packets |
| `description` | string | Bounded job purpose |
| `enabled` | boolean | Disabled templates cannot be selected for new runs |
| `workflow_family` | string | Existing runtime family such as `task` or `incident` |
| `submit_contract` | object | How the job enters `agent.submit` or equivalent wrapper |
| `input_schema` | object | Required and optional input fields plus sensitivity expectations |
| `allowed_profile_ids` | string array | Agent Profiles allowed to run the job |
| `required_capability_packs` | string array | Curated capability packs visible during execution |
| `provider_policy` | object | Local-first and cloud/API constraints |
| `schedule_trigger` | object | External scheduler invocation contract |
| `execution_budget_override` | object | Job-level budget caps or profile-budget constraints |
| `approval_requirements` | object | Approval points required by this job |
| `output_evidence` | object | Required status/events/report/audit outputs |

## Input Schema
The input schema must be compact enough for local LLM execution.

Required input schema fields:
- `required_fields`
- `optional_fields`
- `sensitivity_field`
- `max_payload_bytes`
- `freeform_context_allowed`

Stage 12 policy:
- `freeform_context_allowed` should normally be `false`.
- If free-form context is allowed, the template must define max payload bytes, sensitivity handling, and approval or redaction requirements.
- Upper agents should pass structured inputs, not broad project context dumps.

## Provider Policy
Required provider policy fields:
- `local_first`
- `default_profile_id`
- `allowed_provider_classes`
- `cloud_api_allowed_when`
- `external_send_policy`
- `fallback_profile_id`

Provider policy rules:
- Sensitive or internal jobs should be local-first.
- Cloud/API providers may be allowed only for low sensitivity, public data, or redacted metadata.
- External send must match both the template policy and the selected Agent Profile policy.
- Fallback must preserve status/events/report evidence even when no LLM provider is called.

## Schedule Trigger
NestClaw does not need a full internal scheduler for Stage 12.

Required schedule trigger fields:
- `supported_triggers`
- `invocation_surface`
- `idempotency_key_fields`
- `idempotency_key_policy`
- `examples`

Allowed `supported_triggers` examples:
- `manual`
- `cron`
- `launchd`
- `ci`
- `external_agent`

The trigger must call an existing NestClaw surface such as `agent.submit`, CLI wrapper, HTTP API, or MCP wrapper. It must not call tools directly.

Idempotency policy fields:
- `format`: canonical scheduled key format using the exact placeholders from `idempotency_key_fields`
- `examples`: concrete keys that an operator or upper agent can copy into `--idempotency-key`
- `recommended_duplicate_policy`: one of `run`, `skip`, or `fail`
- `rerun_guidance`: short operator guidance for when to change the key or override duplicate behavior

Explicit scheduled keys should start with `stage12:` and should not include `profile_id`. Business dedupe should survive an approved provider/profile routing change.

## Output Evidence
Required output evidence fields:
- `status_surface`
- `events_surface`
- `report_surface`
- `audit_fields`
- `handoff_included`

Minimum audit fields:
- `task_id`
- `template_id`
- `profile_id`
- `provider_id`
- `capability_packs`
- `execution_budget`
- `approval_queue_id`
- `report_path`

## Runtime Invariants
- A template must reference at least one Agent Profile.
- Each referenced Agent Profile must include the template id in `allowed_job_templates`.
- A template must reference at least one capability pack and must not use wildcard packs.
- A template cannot bypass `agent.submit/status/events/report`.
- A template cannot loosen a profile sensitivity boundary.
- A schedule trigger cannot bypass approval policy.
- A deterministic fallback may run only when its profile is explicitly allowed by the template.

## Existing Surface Mapping
| Template field | Current or planned binding |
| --- | --- |
| `workflow_family` | Existing `task` and `incident` runtime families |
| `submit_contract.surface` | Existing `agent.submit` and future `newclaw job run` wrapper |
| `allowed_profile_ids` | `configs/agent_profiles.json` |
| `required_capability_packs` | Stage 12 Capability Pack spec |
| `provider_policy` | Model registry and Agent Profile sensitivity boundary |
| `approval_requirements` | Existing approval queue and role model |
| `output_evidence` | Existing status/events/report/bundle/handoff surfaces |

## Sample Templates
The baseline registry includes:
- `daily_status_digest`
- `issue_triage`
- `readiness_check`

These samples intentionally cover three patterns:
- local-first internal summarization;
- low-sensitivity cloud/API-optional review with approval;
- deterministic fallback-friendly readiness checking.

Baseline idempotency examples:
- `daily_status_digest`: `stage12:daily_status_digest:daily:2026-04-28:ops_team`
- `issue_triage`: `stage12:issue_triage:issue:redmine:NC-1024:2026-04-28T09`
- `readiness_check`: `stage12:readiness_check:readiness:stage12-scheduler-smoke:stage12:local:2026-04-28`

## Planned Agent-Facing Surfaces
These are planned surfaces, not Stage 12 runtime commitments yet.

- `newclaw jobs list --json`
- `newclaw jobs validate --file configs/job_templates.json`
- `newclaw job run --template <template_id> --profile <profile_id> --input <path>`
- `GET /api/v1/job-templates`
- MCP `job.templates`

## Minimum Stage 12 Baseline
Stage 12 G2 is complete when:
- the template schema is documented here;
- `configs/job_templates.json` contains at least three repeatable jobs;
- templates reference existing Agent Profiles and existing runtime surfaces;
- contract tests prove local-first, cloud/API optionality, schedule trigger, and output evidence are represented.
