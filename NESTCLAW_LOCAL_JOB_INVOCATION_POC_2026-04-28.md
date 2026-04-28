# NestClaw Local Job Invocation PoC

## Purpose
This document records the Stage 12 G4 PoC for running one constrained local-first LLM job through NestClaw's existing orchestration surfaces.

The goal is not to add a human TUI or a second runtime. The goal is to let upper agents, schedulers, and scripts invoke a bounded job template while NestClaw keeps the canonical status, events, report, bundle, and handoff evidence.

## Implemented Surface
Discovery:

```bash
newclaw job list --json
newclaw job describe --template readiness_check --profile local_ops_default --json
newclaw job history --json
python3 -m app.cli job list --json
python3 -m app.cli job describe --template readiness_check --profile local_ops_default --json
python3 -m app.cli job history --json
```

HTTP:

```bash
GET /api/v1/jobs
GET /api/v1/jobs/runs
GET /api/v1/jobs/readiness_check?profile_id=local_ops_default
POST /api/v1/jobs/run
```

MCP:

```text
job.list
job.describe
job.run
job.history
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

Scheduled invocation:

```bash
bash scripts/run_stage12_scheduled_job.sh \
  --template readiness_check \
  --profile local_ops_default \
  --input-file examples/stage12_scheduler/readiness-input.json \
  --requested-by stage12_scheduler \
  --actor-id stage12_scheduler \
  --actor-role requester \
  --idempotency-key readiness-2026-04-28 \
  --duplicate-policy skip \
  --expect-status DONE \
  --include-handoff
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
- execution budget guardrails, including rejected budget overrides, context bytes, and `timeout_seconds`

The executable adapters map onto existing canonical runtimes so the current planner/executor/reporter path remains authoritative.

## Evidence Captured
The JSON response includes:

- `job_invocation`: selected template, profile, provider, capability packs, runtime surfaces, input keys, and budget policy
- `job_invocation.budget_enforcement`: enforced budget fields and observed input size
- `status`: canonical `agent.status` payload
- `events`: canonical `agent.events` payload
- `report`: canonical `agent.report` preview payload
- `bundle`: optional `agent.bundle` evidence when `--include-bundle` is used
- `handoff`: optional `agent.handoff` packet when `--include-handoff` is used

This is the shape expected by Claude/Codex/MCP wrappers, cron/launchd jobs, or other upper agents.

After execution, callers can use `job.history` or `GET /api/v1/jobs/runs` to read the run record without replaying the job.

External schedulers should use `scripts/run_stage12_scheduled_job.sh` or an equivalent wrapper that runs the job and then verifies the resulting `task_id` through job history.

Scheduled callers can pass `--idempotency-key` plus `--duplicate-policy skip` to avoid re-running the same scheduled job. The run payload and history payload both expose `idempotency_key` and `input_fingerprint`.

## Executable Job Adapters
Current executable adapters:

- `daily_status_digest`: internal daily status digest through the existing task runtime.
- `readiness_check`: bounded readiness summary through the existing task runtime, preserving blocked/skipped external env evidence as report content rather than treating readiness as solved.
- `issue_triage`: low-risk issue classification through the existing incident runtime in dry-run mode, preserving ticket draft governance and approval semantics.

## Current Boundary
- Local-first policy is represented by `local_ops_default` and `internal_digest_basic`.
- No cloud/API provider is used for the PoC path.
- Local model server availability is not required; existing provider fallback evidence remains visible in status/events.
- External sends and live tool writes are blocked by the selected template/profile/pack combination unless an existing approval/live-mode path is used separately.
- Input-level budget override is rejected because Stage 12 does not yet provide a human approval path for budget expansion.

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
The completed scheduled invocation wrapper now includes duplicate detection. The next natural follow-up is explicit idempotency key examples per job template and scheduled-run policy review.
