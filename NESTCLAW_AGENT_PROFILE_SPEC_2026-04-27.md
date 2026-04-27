# NestClaw Agent Profile Spec

## Purpose
Agent Profile is the Stage 12 boundary object for local-first LLM job control.

It is not a persona prompt and it is not an agent marketplace entry. It defines which provider or upper-agent wrapper may run which job templates, with which capability packs, budgets, sensitivity limits, approval rules, and audit requirements.

## Canonical Registry
- Draft registry: `configs/agent_profiles.json`
- Status: Stage 12 baseline contract
- Runtime binding: planned after Job Template and Capability Pack specs are stable

## Profile Classes
| provider_class | Use |
| --- | --- |
| `local_llm` | Default path for internal or sensitive work executed by a local provider such as Ollama or LM Studio |
| `cloud_api_llm` | Optional path for low-sensitivity work where policy allows external provider use |
| `upper_agent_wrapper` | A higher-level conversational agent that calls NestClaw instead of bypassing it |
| `deterministic_fallback` | Non-LLM fallback path for degraded or policy-constrained execution |

## Required Fields
| Field | Type | Requirement |
| --- | --- | --- |
| `profile_id` | string | Stable identifier used by job templates and audit evidence |
| `display_name` | string | Human-readable label for dashboard and handoff packets |
| `provider_id` | string | Provider id from model registry or a reserved wrapper/fallback id |
| `provider_class` | enum | One of the profile classes above |
| `enabled` | boolean | Disabled profiles cannot be selected for new runs |
| `owner_role` | string | Role accountable for changing the profile |
| `allowed_job_templates` | string array | Jobs this profile may run |
| `allowed_capability_packs` | string array | Curated packs this profile may use |
| `execution_budget` | object | Tool, retry, time, token, and context limits |
| `sensitivity_boundary` | object | Data sensitivity and external-send boundary |
| `approval_policy` | object | Approval rules for submit, write tools, external send, and budget override |
| `audit_level` | enum | `minimal` or `full`; Stage 12 defaults to `full` |

## Execution Budget
The execution budget must be resolved before planning starts.

Required budget fields:
- `max_tool_calls`
- `max_retries`
- `max_elapsed_seconds`
- `max_provider_tokens`
- `max_context_bytes`
- `allow_network`

Budget override is not a model decision. If a job needs more budget, the run must stop or create an approval item according to `approval_policy.budget_override`.

## Sensitivity Boundary
Required sensitivity fields:
- `allowed_sensitivity`
- `external_send_policy`
- `redaction_required`
- `data_residency`

Allowed `external_send_policy` values:
- `deny`
- `approval_required`
- `allow`

Stage 12 policy:
- `local_llm` is the default for `sensitive_internal` and high-sensitivity work.
- `cloud_api_llm` must not receive sensitive/internal payloads by default.
- `cloud_api_llm` may be used for `public`, `low`, or explicitly redacted metadata when approval policy allows it.
- `upper_agent_wrapper` may submit, inspect, and review through NestClaw, but it must not bypass approval or audit.

## Approval Policy
Required approval policy fields:
- `submit`
- `tool_write`
- `external_send`
- `budget_override`
- `profile_change`

Recommended values:
- `allow`
- `approver_required`
- `admin_required`
- `blocked`

Approval policy is evaluated before execution. Tool draft apply, external send, profile changes, and budget overrides must remain governed by existing requester/approver/admin roles.

## Runtime Invariants
- A profile cannot grant raw tool access. It can only reference curated capability packs.
- A job template must be allowed by the selected profile.
- A capability pack must be allowed by both the selected profile and the job template.
- A local profile should be selected when sensitivity is `sensitive_internal` unless a human-approved exception exists.
- A cloud/API profile must carry provenance and approval evidence when external payload transfer is involved.
- A deterministic fallback profile must not call an LLM provider and must still emit status/events/report evidence.

## Existing Surface Mapping
| Profile field | Current or planned binding |
| --- | --- |
| `provider_id` | `configs/model_registry.yaml` where applicable |
| `allowed_job_templates` | Stage 12 Job Template spec |
| `allowed_capability_packs` | Stage 12 Capability Pack spec and current tool registry |
| `execution_budget` | Planned policy gate before planner/executor |
| `sensitivity_boundary` | Model routing policy plus governance guardrails |
| `approval_policy` | Existing approval queue and role model |
| `audit_level` | Existing status/events/report/handoff evidence |

## Planned Agent-Facing Surfaces
These are planned surfaces, not Stage 12 runtime commitments yet.

- `newclaw profiles list --json`
- `newclaw profiles validate --file configs/agent_profiles.json`
- `GET /api/v1/agent/profiles`
- MCP `agent.profiles`

## Minimum Stage 12 Baseline
Stage 12 G1 is complete when:
- the profile schema is documented here;
- `configs/agent_profiles.json` contains at least local, cloud/API, upper-agent, and deterministic fallback examples;
- contract tests prove local-first and cloud/API sensitivity boundaries are represented;
- later runtime work can validate profiles without changing the vocabulary.
