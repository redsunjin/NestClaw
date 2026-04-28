#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="${NEWCLAW_STAGE12_POC_WORK_DIR:-}"
if [[ -z "$WORK_DIR" ]]; then
  WORK_DIR="$(mktemp -d)"
fi
mkdir -p "$WORK_DIR"

INPUT_FILE="$WORK_DIR/daily-status-input.json"
OUTPUT_FILE="$WORK_DIR/daily-status-output.json"
READINESS_INPUT_FILE="$WORK_DIR/readiness-input.json"
READINESS_OUTPUT_FILE="$WORK_DIR/readiness-output.json"
ISSUE_INPUT_FILE="$WORK_DIR/issue-triage-input.json"
ISSUE_OUTPUT_FILE="$WORK_DIR/issue-triage-output.json"
HISTORY_OUTPUT_FILE="$WORK_DIR/job-history-output.json"

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

cat >"$READINESS_INPUT_FILE" <<'JSON'
{
  "check_set": "stage8-readiness",
  "target_stage": 8,
  "sensitivity": "internal",
  "env_profile": "local",
  "strict_gate": false,
  "timeout_seconds": 15
}
JSON

cat >"$ISSUE_INPUT_FILE" <<'JSON'
{
  "issue_id": "ISSUE-123",
  "summary": "Internal documentation update request needs routing and a safe follow-up ticket draft.",
  "source_system": "helpdesk",
  "sensitivity": "internal",
  "service": "docs-portal",
  "labels": [
    "documentation",
    "low-risk"
  ],
  "recent_events": [
    {
      "timestamp": "2026-04-28T09:00:00Z",
      "status": "new",
      "summary": "Requester attached redacted reproduction notes."
    }
  ],
  "redacted_context": "No customer data included."
}
JSON

python3 -m app.cli job list --json >"$WORK_DIR/job-list.json"
python3 -m app.cli job describe \
  --template readiness_check \
  --profile local_ops_default \
  --json >"$WORK_DIR/readiness-describe.json"

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

python3 -m app.cli job run \
  --template readiness_check \
  --profile local_ops_default \
  --input-file "$READINESS_INPUT_FILE" \
  --requested-by stage12_poc \
  --actor-id stage12_poc \
  --actor-role requester \
  --include-bundle \
  --include-handoff \
  --max-chars 2400 \
  --json >"$READINESS_OUTPUT_FILE"

python3 -m app.cli job run \
  --template issue_triage \
  --profile local_ops_default \
  --input-file "$ISSUE_INPUT_FILE" \
  --requested-by stage12_poc \
  --actor-id stage12_poc \
  --actor-role requester \
  --include-bundle \
  --include-handoff \
  --max-chars 2400 \
  --json >"$ISSUE_OUTPUT_FILE"

python3 -m app.cli job history \
  --actor-id stage12_poc \
  --actor-role requester \
  --limit 10 \
  --json >"$HISTORY_OUTPUT_FILE"

python3 - "$OUTPUT_FILE" "$READINESS_OUTPUT_FILE" "$ISSUE_OUTPUT_FILE" "$HISTORY_OUTPUT_FILE" "$WORK_DIR/job-list.json" "$WORK_DIR/readiness-describe.json" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

daily_payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
readiness_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
issue_payload = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
history_payload = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
job_list = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))
readiness_describe = json.loads(Path(sys.argv[6]).read_text(encoding="utf-8"))

listed = {item["template_id"]: item for item in job_list["items"]}
if not listed["daily_status_digest"]["executable"]:
    raise SystemExit("daily_status_digest should be executable")
if not listed["readiness_check"]["executable"]:
    raise SystemExit("readiness_check should be executable")
if not listed["issue_triage"]["executable"]:
    raise SystemExit("issue_triage should be executable")
if readiness_describe["template"]["required_capability_packs"] != ["readiness_probe_readonly", "core_status_readonly"]:
    raise SystemExit("unexpected readiness capability pack binding")

for expected_template, payload in [
    ("daily_status_digest", daily_payload),
    ("readiness_check", readiness_payload),
    ("issue_triage", issue_payload),
]:
    status = payload["status"]
    invocation = payload["job_invocation"]
    if status["status"] != "DONE":
        raise SystemExit(f"{expected_template}: expected DONE, got {status['status']}")
    if invocation["template_id"] != expected_template:
        raise SystemExit(f"unexpected template: {invocation['template_id']}")
    if payload["events"]["count"] < 4:
        raise SystemExit(f"{expected_template}: expected at least four runtime events")
    report_path = Path(str(status["result"]["report_path"]))
    if not report_path.is_file():
        raise SystemExit(f"{expected_template}: report missing: {report_path}")
    if payload["handoff"]["packet_type"] != "completed":
        raise SystemExit(f"{expected_template}: unexpected handoff packet: {payload['handoff']['packet_type']}")

if issue_payload["status"]["resolved_kind"] != "incident":
    raise SystemExit("issue_triage should run through the incident workflow")
if issue_payload["status"]["run_mode"] != "dry-run":
    raise SystemExit("issue_triage should remain dry-run in the PoC")
expected_task_ids = {
    daily_payload["status"]["task_id"],
    readiness_payload["status"]["task_id"],
    issue_payload["status"]["task_id"],
}
history_task_ids = {item["task_id"] for item in history_payload["items"]}
if not expected_task_ids.issubset(history_task_ids):
    raise SystemExit("job history should include all PoC job runs")

print(
    "[OK] stage12 local job poc "
    f"daily_task_id={daily_payload['status']['task_id']} "
    f"readiness_task_id={readiness_payload['status']['task_id']} "
    f"issue_task_id={issue_payload['status']['task_id']} "
    f"work_dir={Path(sys.argv[1]).parent}"
)
PY
