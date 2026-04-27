# NestClaw Local Job Invocation PoC

## Purpose
This document records the Stage 12 G4 PoC for running one constrained local-first LLM job through NestClaw's existing orchestration surfaces.

The goal is not to add a human TUI or a second runtime. The goal is to let upper agents, schedulers, and scripts invoke a bounded job template while NestClaw keeps the canonical status, events, report, bundle, and handoff evidence.

## Implemented Surface
Discovery:

```bash
newclaw job list --json
newclaw job describe --template readiness_check --profile local_ops_default --json
python3 -m app.cli job list --json
python3 -m app.cli job describe --template readiness_check --profile local_ops_default --json
```

HTTP:

```bash
GET /api/v1/jobs
GET /api/v1/jobs/readiness_check?profile_id=local_ops_default
POST /api/v1/jobs/run
```

MCP:

```text
job.list
job.describe
job.run
```

CLI:

```bash
python3 -m app.cli job run \
  --template daily_status_digest \
  --profile local_ops_default \
  --input-file daily-status-input.json \
  --requested-by ops_user \
  --actor-id ops_user \
  --actor-role requester \
  --include-bundle \
  --include-handoff \
  --json
```

Scripted smoke:

```bash
bash scripts/run_stage12_local_job_poc.sh
```

## Contract Resolution
Before runtime submission, `newclaw job run` validates:

- `configs/job_templates.json`
- `configs/agent_profiles.json`
- `configs/capability_packs.json`
- required input fields
- profile-to-template allowlist
- template-to-profile allowlist
- required capability packs
- pack-to-profile and pack-to-template allowlists
- sensitivity boundary for the selected profile and packs

For the PoC, only `daily_status_digest` is implemented as an executable job adapter. It maps to the existing `meeting_summary` task runtime so the current planner/executor/reporter path remains canonical.

## Evidence Captured
The JSON response includes:

- `job_invocation`: selected template, profile, provider, capability packs, runtime surfaces, input keys, and budget policy
- `status`: canonical `agent.status` payload
- `events`: canonical `agent.events` payload
- `report`: canonical `agent.report` preview payload
- `bundle`: optional `agent.bundle` evidence when `--include-bundle` is used
- `handoff`: optional `agent.handoff` packet when `--include-handoff` is used

This is the shape expected by Claude/Codex/MCP wrappers, cron/launchd jobs, or other upper agents.

## Executable Job Adapters
Current executable adapters:

- `daily_status_digest`: internal daily status digest through the existing task runtime.
- `readiness_check`: bounded readiness summary through the existing task runtime, preserving blocked/skipped external env evidence as report content rather than treating readiness as solved.

Planned but not yet executable:

- `issue_triage`: still requires a separate incident-oriented adapter decision because it may involve ticket draft governance.

## Current Boundary
- Local-first policy is represented by `local_ops_default` and `internal_digest_basic`.
- No cloud/API provider is used for the PoC path.
- Local model server availability is not required; existing provider fallback evidence remains visible in status/events.
- External sends and tool writes are blocked by the selected template/profile/pack combination.

## Verification
Primary tests:

```bash
python3 -m unittest tests.test_stage12_contract tests.test_stage12_job_invocation_smoke
```

Cycle gate:

```bash
env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH \
  NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 \
  NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 \
  bash scripts/run_dev_qa_cycle.sh 12
```

## Next Step
The next natural step is to expose the same discovery payload through MCP/HTTP, then decide whether dashboard chat should call this same job surface rather than inventing a separate chat runtime.
