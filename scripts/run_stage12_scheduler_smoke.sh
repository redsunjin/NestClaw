#!/usr/bin/env bash
set -euo pipefail

ARGS=(
  --template readiness_check
  --profile local_ops_default
  --input-file examples/stage12_scheduler/readiness-input.json
  --requested-by stage12_scheduler_smoke
  --actor-id stage12_scheduler_smoke
  --actor-role requester
  --expect-status DONE
  --max-chars 2400
  --include-bundle
  --include-handoff
)

if [[ -n "${NEWCLAW_STAGE12_SCHEDULER_SMOKE_WORK_DIR:-}" ]]; then
  ARGS+=(--work-dir "$NEWCLAW_STAGE12_SCHEDULER_SMOKE_WORK_DIR")
fi

bash scripts/run_stage12_scheduled_job.sh "${ARGS[@]}"
