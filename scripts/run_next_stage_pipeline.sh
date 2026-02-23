#!/usr/bin/env bash
set -euo pipefail

TARGET_STAGE="${1:-6}"
MAX_ROUNDS="${2:-5}"
SLEEP_SECONDS="${3:-3}"

echo "[1/4] Documentation audit"
bash scripts/run_doc_audit.sh

echo "[2/4] Expert QA"
bash scripts/run_expert_qa.sh

echo "[3/4] Auto cycle"
bash scripts/run_auto_cycle.sh "$TARGET_STAGE" "$MAX_ROUNDS" "$SLEEP_SECONDS"

echo "[4/4] Completed next-stage automation pipeline."
