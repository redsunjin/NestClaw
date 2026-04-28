#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/run_stage12_scheduled_job.sh \
  --template <template_id> \
  --profile <profile_id> \
  --input-file <input.json> \
  [--requested-by <id>] \
  [--actor-id <id>] \
  [--actor-role <role>] \
  [--expect-status <status>] \
  [--work-dir <dir>] \
  [--max-chars <n>] \
  [--include-bundle] \
  [--include-handoff]

Runs one Stage 12 job through the canonical CLI, reads job history, and writes
run/history/input evidence into a scheduler-owned report directory.
EOF
}

TEMPLATE_ID=""
PROFILE_ID=""
INPUT_FILE=""
REQUESTED_BY="${NEWCLAW_STAGE12_SCHEDULER_REQUESTED_BY:-stage12_scheduler}"
ACTOR_ID="${NEWCLAW_STAGE12_SCHEDULER_ACTOR_ID:-}"
ACTOR_ROLE="${NEWCLAW_STAGE12_SCHEDULER_ACTOR_ROLE:-requester}"
EXPECT_STATUS="${NEWCLAW_STAGE12_SCHEDULER_EXPECT_STATUS:-DONE}"
WORK_DIR="${NEWCLAW_STAGE12_SCHEDULER_WORK_DIR:-}"
MAX_CHARS="${NEWCLAW_STAGE12_SCHEDULER_MAX_CHARS:-2400}"
INCLUDE_BUNDLE=0
INCLUDE_HANDOFF=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --template)
      TEMPLATE_ID="${2:-}"
      shift 2
      ;;
    --profile)
      PROFILE_ID="${2:-}"
      shift 2
      ;;
    --input-file|--input)
      INPUT_FILE="${2:-}"
      shift 2
      ;;
    --requested-by)
      REQUESTED_BY="${2:-}"
      shift 2
      ;;
    --actor-id)
      ACTOR_ID="${2:-}"
      shift 2
      ;;
    --actor-role)
      ACTOR_ROLE="${2:-}"
      shift 2
      ;;
    --expect-status)
      EXPECT_STATUS="${2:-}"
      shift 2
      ;;
    --work-dir)
      WORK_DIR="${2:-}"
      shift 2
      ;;
    --max-chars)
      MAX_CHARS="${2:-}"
      shift 2
      ;;
    --include-bundle)
      INCLUDE_BUNDLE=1
      shift
      ;;
    --include-handoff)
      INCLUDE_HANDOFF=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$TEMPLATE_ID" || -z "$PROFILE_ID" || -z "$INPUT_FILE" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Input file not found: $INPUT_FILE" >&2
  exit 2
fi

if [[ -z "$ACTOR_ID" ]]; then
  ACTOR_ID="$REQUESTED_BY"
fi

if [[ -z "$WORK_DIR" ]]; then
  SAFE_TEMPLATE="$(printf "%s" "$TEMPLATE_ID" | tr -cs '[:alnum:]_.-' '-')"
  STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
  WORK_DIR="reports/stage12-scheduled-runs/${STAMP}-${SAFE_TEMPLATE}"
fi
mkdir -p "$WORK_DIR"

RUN_OUTPUT="$WORK_DIR/job-run.json"
HISTORY_OUTPUT="$WORK_DIR/job-history.json"
SUMMARY_OUTPUT="$WORK_DIR/summary.json"
INPUT_COPY="$WORK_DIR/input.json"
cp "$INPUT_FILE" "$INPUT_COPY"

RUN_CMD=(
  python3 -m app.cli job run
  --template "$TEMPLATE_ID"
  --profile "$PROFILE_ID"
  --input-file "$INPUT_FILE"
  --requested-by "$REQUESTED_BY"
  --actor-id "$ACTOR_ID"
  --actor-role "$ACTOR_ROLE"
  --max-chars "$MAX_CHARS"
  --json
)
if [[ "$INCLUDE_BUNDLE" == "1" ]]; then
  RUN_CMD+=(--include-bundle)
fi
if [[ "$INCLUDE_HANDOFF" == "1" ]]; then
  RUN_CMD+=(--include-handoff)
fi

"${RUN_CMD[@]}" >"$RUN_OUTPUT"

python3 -m app.cli job history \
  --template "$TEMPLATE_ID" \
  --actor-id "$ACTOR_ID" \
  --actor-role "$ACTOR_ROLE" \
  --limit 20 \
  --json >"$HISTORY_OUTPUT"

python3 - "$RUN_OUTPUT" "$HISTORY_OUTPUT" "$SUMMARY_OUTPUT" "$EXPECT_STATUS" "$TEMPLATE_ID" "$PROFILE_ID" "$WORK_DIR" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

run_path = Path(sys.argv[1])
history_path = Path(sys.argv[2])
summary_path = Path(sys.argv[3])
expected_status = sys.argv[4]
expected_template = sys.argv[5]
expected_profile = sys.argv[6]
work_dir = Path(sys.argv[7])

run_payload = json.loads(run_path.read_text(encoding="utf-8"))
history_payload = json.loads(history_path.read_text(encoding="utf-8"))

if "error" in run_payload:
    raise SystemExit(f"job run failed: {run_payload['error']}")
if "error" in history_payload:
    raise SystemExit(f"job history failed: {history_payload['error']}")

invocation = run_payload["job_invocation"]
status = run_payload["status"]
actual_status = str(status.get("status") or "")
task_id = str(status.get("task_id") or invocation.get("task_id") or "")

if actual_status != expected_status:
    raise SystemExit(f"expected status {expected_status}, got {actual_status}")
if invocation.get("template_id") != expected_template:
    raise SystemExit(f"expected template {expected_template}, got {invocation.get('template_id')}")
if invocation.get("profile_id") != expected_profile:
    raise SystemExit(f"expected profile {expected_profile}, got {invocation.get('profile_id')}")
if not task_id:
    raise SystemExit("job run did not expose task_id")

history_items = history_payload.get("items") or []
history_by_task = {str(item.get("task_id") or ""): item for item in history_items}
if task_id not in history_by_task:
    raise SystemExit(f"job history did not include task_id={task_id}")

report_path = Path(str(status.get("result", {}).get("report_path") or ""))
if not report_path.is_file():
    raise SystemExit(f"report missing: {report_path}")

summary = {
    "surface": "stage12.scheduled_job",
    "template_id": invocation.get("template_id"),
    "profile_id": invocation.get("profile_id"),
    "provider_class": invocation.get("provider_class"),
    "task_id": task_id,
    "status": actual_status,
    "report_path": str(report_path),
    "history_count": len(history_items),
    "work_dir": str(work_dir),
    "evidence_files": {
        "input": str(work_dir / "input.json"),
        "run": str(run_path),
        "history": str(history_path),
        "summary": str(summary_path),
    },
}
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(
    "[OK] stage12 scheduled job "
    f"template={summary['template_id']} "
    f"profile={summary['profile_id']} "
    f"task_id={task_id} "
    f"status={actual_status} "
    f"work_dir={work_dir}"
)
PY
