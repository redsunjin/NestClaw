#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERT_WORKFLOW="$SCRIPT_DIR/run_expert_agent_workflow.sh"
CAMPAIGN_ROOT="work/priority_campaigns"

usage() {
  cat <<EOF
Usage:
  $0 status <campaign-id>
  $0 start-next <campaign-id> [target-stage]
  $0 advance <campaign-id> <item-id> <unit-id> [target-stage]
EOF
}

campaign_file() {
  printf "%s/%s/campaign.json" "$CAMPAIGN_ROOT" "$1"
}

require_campaign() {
  local file
  file="$(campaign_file "$1")"
  if [[ ! -f "$file" ]]; then
    echo "[ERROR] campaign file not found: $file"
    exit 1
  fi
}

status_cmd() {
  local campaign_id="$1"
  require_campaign "$campaign_id"
  python3 - "$campaign_id" <<'PY'
import json, sys
from pathlib import Path

campaign_id = sys.argv[1]
path = Path("work/priority_campaigns") / campaign_id / "campaign.json"
data = json.loads(path.read_text(encoding="utf-8"))
items = data["items"]
active = next((item for item in items if item["status"] == "in_progress"), None)
pending = next((item for item in items if item["status"] == "pending"), None)
completed = [item for item in items if item["status"] == "completed"]
print(f"campaign_id: {data['campaign_id']}")
print(f"goal: {data['goal']}")
print(f"target_stage: {data.get('target_stage', 8)}")
print(f"completed_count: {len(completed)}")
if active:
    print(f"current_item: {active['item_id']}")
    print(f"current_unit: {active['unit_id']}")
elif pending:
    print("current_item: none")
    print(f"next_item: {pending['item_id']}")
    print(f"next_unit: {pending['unit_id']}")
else:
    print("campaign_state: completed")
PY
}

start_next_cmd() {
  local campaign_id="$1"
  local stage="${2:-8}"
  require_campaign "$campaign_id"
  local out
  out="$(python3 - "$campaign_id" <<'PY'
import json, sys
from pathlib import Path

campaign_id = sys.argv[1]
path = Path("work/priority_campaigns") / campaign_id / "campaign.json"
data = json.loads(path.read_text(encoding="utf-8"))
items = data["items"]
active = next((item for item in items if item["status"] == "in_progress"), None)
if active:
    print(f"{active['unit_id']}\n{active['goal']}\nALREADY_ACTIVE")
    raise SystemExit(0)
pending = next((item for item in items if item["status"] == "pending"), None)
if not pending:
    print("\n\nCAMPAIGN_DONE")
    raise SystemExit(0)
pending["status"] = "in_progress"
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{pending['unit_id']}\n{pending['goal']}\nSTARTED")
PY
)"
  local unit goal state
  unit="$(printf "%s" "$out" | sed -n '1p')"
  goal="$(printf "%s" "$out" | sed -n '2p')"
  state="$(printf "%s" "$out" | sed -n '3p')"
  if [[ "$state" == "CAMPAIGN_DONE" ]]; then
    echo "[OK] campaign completed"
    exit 0
  fi
  if [[ "$state" == "ALREADY_ACTIVE" ]]; then
    echo "[OK] active item already exists: $unit"
    exit 0
  fi
  bash "$EXPERT_WORKFLOW" prepare "$unit" "$goal" "$stage"
}

advance_cmd() {
  local campaign_id="$1"
  local item_id="$2"
  local unit_id="$3"
  local stage="${4:-8}"
  require_campaign "$campaign_id"
  if [[ ! -f "work/micro_units/${unit_id}/WORK_UNIT.md" ]]; then
    echo "[ERROR] MWU file not found: work/micro_units/${unit_id}/WORK_UNIT.md"
    exit 1
  fi
  if ! rg -q --fixed-strings -- "- status: \`DONE\`" "work/micro_units/${unit_id}/WORK_UNIT.md"; then
    echo "[ERROR] MWU is not DONE: ${unit_id}"
    exit 1
  fi
  local out
  out="$(python3 - "$campaign_id" "$item_id" "$unit_id" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path

campaign_id, item_id, unit_id = sys.argv[1:4]
path = Path("work/priority_campaigns") / campaign_id / "campaign.json"
data = json.loads(path.read_text(encoding="utf-8"))
items = data["items"]
target = next((item for item in items if item["item_id"] == item_id), None)
if target is None:
    raise SystemExit(f"[ERROR] campaign item not found: {item_id}")
if target["unit_id"] != unit_id:
    raise SystemExit(f"[ERROR] campaign item {item_id} is linked to {target['unit_id']}, not {unit_id}")
target["status"] = "completed"
target["completed_unit_id"] = unit_id
target["completed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
next_pending = next((item for item in items if item["status"] == "pending"), None)
if next_pending:
    next_pending["status"] = "in_progress"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{next_pending['unit_id']}\n{next_pending['goal']}\nNEXT_READY")
else:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n\nCAMPAIGN_DONE")
PY
)"
  local unit goal state
  unit="$(printf "%s" "$out" | sed -n '1p')"
  goal="$(printf "%s" "$out" | sed -n '2p')"
  state="$(printf "%s" "$out" | sed -n '3p')"
  if [[ "$state" == "CAMPAIGN_DONE" ]]; then
    echo "[OK] campaign completed"
    exit 0
  fi
  bash "$EXPERT_WORKFLOW" prepare "$unit" "$goal" "$stage"
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    status)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      status_cmd "$2"
      ;;
    start-next)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      start_next_cmd "$2" "${3:-8}"
      ;;
    advance)
      [[ $# -ge 4 ]] || { usage; exit 1; }
      advance_cmd "$2" "$3" "$4" "${5:-8}"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
