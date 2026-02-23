#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage:
  $0 <target-stage:1..7> [max-rounds] [sleep-seconds] [--fix-cmd "<command>"]

Examples:
  $0 4
  $0 6 8 5
  $0 6 10 3 --fix-cmd "echo 'manual fix required'"
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

TARGET_STAGE="${1:-}"
MAX_ROUNDS="${2:-10}"
SLEEP_SECONDS="${3:-3}"
FIX_CMD=""

if [[ -z "$TARGET_STAGE" ]]; then
  usage
  exit 2
fi

if ! [[ "$TARGET_STAGE" =~ ^[1-7]$ ]]; then
  echo "target-stage must be 1..7"
  exit 2
fi

if ! [[ "$MAX_ROUNDS" =~ ^[0-9]+$ ]] || [[ "$MAX_ROUNDS" -lt 1 ]]; then
  echo "max-rounds must be >= 1"
  exit 2
fi

if ! [[ "$SLEEP_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "sleep-seconds must be >= 0"
  exit 2
fi

if [[ "${4:-}" == "--fix-cmd" ]]; then
  FIX_CMD="${5:-}"
  if [[ -z "$FIX_CMD" ]]; then
    echo "--fix-cmd requires a command string"
    exit 2
  fi
fi

ROUND=1
LAST_REPORT=""

echo "Auto cycle start: target_stage=${TARGET_STAGE}, max_rounds=${MAX_ROUNDS}, sleep=${SLEEP_SECONDS}s"

while [[ "$ROUND" -le "$MAX_ROUNDS" ]]; do
  echo ""
  echo "== Round ${ROUND}/${MAX_ROUNDS} =="

  set +e
  OUTPUT="$(bash scripts/run_dev_qa_cycle.sh "$TARGET_STAGE" 2>&1)"
  RC=$?
  set -e

  echo "$OUTPUT"
  LAST_REPORT="$(echo "$OUTPUT" | sed -n 's/^- report: //p' | tail -n 1)"

  if [[ "$RC" -eq 0 ]]; then
    echo ""
    echo "Auto cycle success at round ${ROUND}."
    if [[ -n "$LAST_REPORT" ]]; then
      echo "Last report: ${LAST_REPORT}"
    fi
    exit 0
  fi

  echo ""
  echo "Round ${ROUND} failed."
  if [[ -n "$LAST_REPORT" ]]; then
    echo "Last report: ${LAST_REPORT}"
  fi

  if [[ -n "$FIX_CMD" ]]; then
    echo "Running fix command..."
    set +e
    bash -lc "$FIX_CMD"
    FIX_RC=$?
    set -e
    if [[ "$FIX_RC" -ne 0 ]]; then
      echo "Fix command failed with exit code ${FIX_RC}. Stopping."
      exit "$FIX_RC"
    fi
  else
    echo "No --fix-cmd provided. Stopping after first failed round."
    exit "$RC"
  fi

  ROUND=$((ROUND + 1))
  if [[ "$ROUND" -le "$MAX_ROUNDS" ]]; then
    sleep "$SLEEP_SECONDS"
  fi
done

echo ""
echo "Auto cycle reached max rounds (${MAX_ROUNDS}) without full success."
if [[ -n "$LAST_REPORT" ]]; then
  echo "Last report: ${LAST_REPORT}"
fi
exit 1
