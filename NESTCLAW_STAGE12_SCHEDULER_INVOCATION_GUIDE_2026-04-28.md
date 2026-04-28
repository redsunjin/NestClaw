# NestClaw Stage 12 Scheduler Invocation Guide

## Purpose
Stage 12 does not add a built-in scheduler. The scheduler boundary is intentionally external: cron, launchd, CI, or an upper agent decides when to run; NestClaw decides whether the job contract is valid, executes it through the canonical runtime, and records evidence.

This keeps NestClaw focused as a local-first LLM job control plane instead of becoming another calendar or queue service.

## Canonical Wrapper
Use:

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

The wrapper performs the same actions every external scheduler should perform:

- call `python3 -m app.cli job run`
- call `python3 -m app.cli job history`
- preserve `idempotency_key` and `input_fingerprint` in run/history evidence
- verify the returned `task_id` appears in history
- verify the job reached the expected status, usually `DONE`
- write `input.json`, `job-run.json`, `job-history.json`, and `summary.json` under `reports/stage12-scheduled-runs/`

## Duplicate Policy
The wrapper supports three duplicate policies:

- `run`: always run a new job and record idempotency evidence. This is the default for backwards-compatible manual use.
- `skip`: check `job.history` first; if the same `idempotency_key` already exists, write `summary.json` with `SKIPPED_DUPLICATE` and exit successfully.
- `fail`: check `job.history` first; if the same `idempotency_key` already exists, fail the scheduler command.

If `--idempotency-key` is omitted, the wrapper derives one from template, profile, and canonical input JSON. For real business schedules, prefer an explicit key such as `daily-status-2026-04-28` or `readiness-stage12-2026-04-28`.

## Supported External Schedulers
Examples for cron, launchd, and GitHub Actions live in `examples/stage12_scheduler/`:

- `cron.example`
- `launchd.local.example.plist`
- `github-actions.example.yml`
- `daily-status-input.json`
- `readiness-input.json`

These examples are integration templates, not active project automation. Copying one into a real scheduler should be treated as an environment handoff decision.

## Contract Boundary
Scheduler invocation must not bypass:

- `configs/job_templates.json`
- `configs/agent_profiles.json`
- `configs/capability_packs.json`
- profile/template/pack allowlists
- sensitivity boundary checks
- execution budget guardrails
- canonical `agent.status`, `agent.events`, `agent.report`, `agent.bundle`, and `agent.handoff` evidence

The scheduler should not call lower-level task or incident endpoints directly. It should call the job wrapper or equivalent HTTP/MCP job surfaces.

## Verification
Smoke check:

```bash
bash scripts/run_stage12_scheduler_smoke.sh
bash scripts/run_stage12_scheduler_dedupe_smoke.sh
```

Stage 12 cycle:

```bash
env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH \
  NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=30 \
  NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 \
  bash scripts/run_dev_qa_cycle.sh 12
```

## Design Decision
NestClaw stores run evidence, not schedule ownership. This is the right split for small organizations and clubs because it keeps setup simple while still giving local LLM jobs a safe, repeatable execution contract.
