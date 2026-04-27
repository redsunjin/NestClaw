# NestClaw Capability Pack Spec

## Purpose
Capability Pack is the Stage 12 allowlist boundary between a selected Job Template, a selected Agent Profile, and the tool registry.

It is not a marketplace package and it is not an unrestricted tool discovery surface. It defines exactly which tool ids, runtime read surfaces, approval rules, data boundaries, and profile/template bindings are visible to an LLM-backed job.

## Canonical Registry
- Draft registry: `configs/capability_packs.json`
- Status: Stage 12 baseline contract
- Depends on:
  - `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
  - `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
  - `configs/tool_registry.yaml`
- Runtime enforcement: planned after local job invocation payloads are stable

## Required Fields
| Field | Type | Requirement |
| --- | --- | --- |
| `pack_id` | string | Stable id referenced by Agent Profiles and Job Templates |
| `display_name` | string | Human-readable label for dashboard and handoff packets |
| `description` | string | Bounded pack purpose |
| `enabled` | boolean | Disabled packs cannot be selected for new runs |
| `pack_type` | enum | `tool_allowlist`, `runtime_readonly`, or `draft_ops` |
| `risk_level` | enum | `low`, `medium`, `high`, or `critical` |
| `allowed_tool_ids` | string array | Explicit tool ids from `configs/tool_registry.yaml`; wildcard ids are forbidden |
| `denied_tool_ids` | string array | Explicit tools that remain hidden even if present elsewhere |
| `runtime_read_surfaces` | string array | Read-only NestClaw surfaces allowed without tool invocation |
| `approval_requirements` | object | Approval rules for read, write, external send, dry-run, and pack change |
| `data_boundary` | object | Sensitivity, external systems, external send, and redaction rules |
| `allowed_profile_ids` | string array | Agent Profiles allowed to use this pack |
| `allowed_template_ids` | string array | Job Templates allowed to request this pack |
| `audit_fields` | string array | Evidence fields that must be recorded when the pack is used |

## Pack Types
| pack_type | Meaning |
| --- | --- |
| `tool_allowlist` | Gives a bounded tool subset to planner/executor |
| `runtime_readonly` | Gives read-only status/event/report/capability surfaces, with no external tool write |
| `draft_ops` | Allows draft/write-capable operations only under approval or dry-run policy |

## Approval Requirements
Required approval fields:
- `tool_read`
- `tool_write`
- `external_send`
- `dry_run_required`
- `pack_change`

Recommended values:
- `allow`
- `approver_required`
- `admin_required`
- `blocked`

Approval rule:
- The effective runtime policy must choose the strictest rule across Agent Profile, Job Template, Capability Pack, and underlying tool defaults.
- A pack cannot lower approval requirements from a tool, profile, or template.

## Data Boundary
Required data boundary fields:
- `allowed_sensitivity`
- `external_systems`
- `external_send_policy`
- `redaction_required`
- `data_residency`

Stage 12 policy:
- Packs used by local/internal jobs may allow `internal` and `sensitive_internal` only when `external_send_policy` is `deny`.
- Packs used by cloud/API profiles must be limited to `public`, `low`, or `redacted_metadata` unless a later explicit exception exists.
- Packs that reference `slack` or `redmine` tools must require approval or dry-run behavior before external side effects.

## Runtime Invariants
- A pack id must resolve from every Agent Profile and Job Template reference.
- Every `allowed_tool_ids` and `denied_tool_ids` entry must exist in `configs/tool_registry.yaml`.
- Wildcard ids such as `*` are forbidden.
- A Job Template can use a pack only if the selected Agent Profile also allows that pack.
- A pack cannot add tools to a cloud/API profile that are outside the profile's sensitivity boundary.
- Runtime read surfaces are not direct tool execution and must still appear in audit evidence.
- Pack changes require admin-level approval or an equivalent tool draft governance flow.

## Existing Surface Mapping
| Pack field | Current or planned binding |
| --- | --- |
| `allowed_tool_ids` | Current `configs/tool_registry.yaml` |
| `runtime_read_surfaces` | Existing `agent.status`, `agent.events`, `agent.report`, `catalog.manifest`, bundle/handoff surfaces |
| `allowed_profile_ids` | `configs/agent_profiles.json` |
| `allowed_template_ids` | `configs/job_templates.json` |
| `approval_requirements` | Existing approval queue and role model |
| `audit_fields` | Existing status/events/report/bundle/handoff evidence |

## Baseline Packs
The baseline registry includes:
- `internal_digest_basic`
- `readiness_probe_readonly`
- `doc_review_readonly`
- `nestclaw_control_readonly`
- `core_status_readonly`
- `issue_triage_readonly`
- `ticket_draft_ops`

## Minimum Stage 12 Baseline
Stage 12 G3 is complete when:
- the pack schema is documented here;
- `configs/capability_packs.json` resolves all pack ids from Agent Profiles and Job Templates;
- pack tool ids resolve to the current tool registry;
- contract tests prove pack/profile/template/tool cross-reference consistency.
