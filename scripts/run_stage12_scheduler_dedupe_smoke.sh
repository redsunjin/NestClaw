#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
KEY="stage12:readiness_check:readiness:stage12-dedupe-smoke:stage12:local:${STAMP}-$$"
BASE_WORK_DIR="${NEWCLAW_STAGE12_SCHEDULER_DEDUPE_WORK_DIR:-reports/stage12-scheduler-dedupe-smoke/${STAMP}-$$}"

mkdir -p "$BASE_WORK_DIR"

bash scripts/run_stage12_scheduled_job.sh \
  --template readiness_check \
  --profile local_ops_default \
  --input-file examples/stage12_scheduler/readiness-input.json \
  --requested-by stage12_scheduler_dedupe_smoke \
  --actor-id stage12_scheduler_dedupe_smoke \
  --actor-role requester \
  --expect-status DONE \
  --idempotency-key "$KEY" \
  --duplicate-policy fail \
  --work-dir "$BASE_WORK_DIR/first" \
  --include-handoff >"$BASE_WORK_DIR/first.out"

bash scripts/run_stage12_scheduled_job.sh \
  --template readiness_check \
  --profile local_ops_default \
  --input-file examples/stage12_scheduler/readiness-input.json \
  --requested-by stage12_scheduler_dedupe_smoke \
  --actor-id stage12_scheduler_dedupe_smoke \
  --actor-role requester \
  --expect-status DONE \
  --idempotency-key "$KEY" \
  --duplicate-policy skip \
  --work-dir "$BASE_WORK_DIR/second" \
  --include-handoff >"$BASE_WORK_DIR/second.out"

python3 - "$BASE_WORK_DIR" "$KEY" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

base = Path(sys.argv[1])
expected_key = sys.argv[2]
first = json.loads((base / "first" / "summary.json").read_text(encoding="utf-8"))
second = json.loads((base / "second" / "summary.json").read_text(encoding="utf-8"))

if first.get("idempotency_key") != expected_key:
    raise SystemExit("first run did not preserve idempotency key")
if first.get("status") != "DONE":
    raise SystemExit(f"first run should be DONE, got {first.get('status')}")
if second.get("idempotency_key") != expected_key:
    raise SystemExit("duplicate skip did not preserve idempotency key")
if second.get("status") != "SKIPPED_DUPLICATE":
    raise SystemExit(f"second run should skip duplicate, got {second.get('status')}")
if second.get("duplicate_task_id") != first.get("task_id"):
    raise SystemExit("duplicate skip should point to first task")

print(
    "[OK] stage12 scheduler dedupe smoke "
    f"idempotency_key={expected_key} "
    f"first_task_id={first.get('task_id')} "
    f"work_dir={base}"
)
PY
