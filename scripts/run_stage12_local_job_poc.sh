#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="${NEWCLAW_STAGE12_POC_WORK_DIR:-}"
if [[ -z "$WORK_DIR" ]]; then
  WORK_DIR="$(mktemp -d)"
fi
mkdir -p "$WORK_DIR"

INPUT_FILE="$WORK_DIR/daily-status-input.json"
OUTPUT_FILE="$WORK_DIR/daily-status-output.json"

cat >"$INPUT_FILE" <<'JSON'
{
  "date": "2026-04-28",
  "audience": "ops_team",
  "sensitivity": "internal",
  "sources": [
    {
      "name": "standup",
      "status": "on_track",
      "summary": "Stage 12 local job invocation uses the existing agent runtime."
    },
    {
      "name": "qa",
      "status": "watch",
      "summary": "The PoC records status, events, report, bundle, and handoff evidence."
    }
  ],
  "focus_areas": [
    "job invocation",
    "audit evidence"
  ],
  "excluded_topics": [
    "cloud relay"
  ]
}
JSON

python3 -m app.cli job run \
  --template daily_status_digest \
  --profile local_ops_default \
  --input-file "$INPUT_FILE" \
  --requested-by stage12_poc \
  --actor-id stage12_poc \
  --actor-role requester \
  --include-bundle \
  --include-handoff \
  --max-chars 2400 \
  --json >"$OUTPUT_FILE"

python3 - "$OUTPUT_FILE" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
status = payload["status"]
invocation = payload["job_invocation"]
if status["status"] != "DONE":
    raise SystemExit(f"expected DONE, got {status['status']}")
if invocation["template_id"] != "daily_status_digest":
    raise SystemExit(f"unexpected template: {invocation['template_id']}")
if payload["events"]["count"] < 4:
    raise SystemExit("expected at least four runtime events")
report_path = Path(str(status["result"]["report_path"]))
if not report_path.is_file():
    raise SystemExit(f"report missing: {report_path}")
if payload["handoff"]["packet_type"] != "completed":
    raise SystemExit(f"unexpected handoff packet: {payload['handoff']['packet_type']}")
print(f"[OK] stage12 local job poc task_id={status['task_id']} output={sys.argv[1]}")
PY
