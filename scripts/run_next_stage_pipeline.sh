#!/usr/bin/env bash
set -euo pipefail

TARGET_STAGE="${1:-7}"
MAX_ROUNDS="${2:-5}"
SLEEP_SECONDS="${3:-3}"
PLAN_FILE="${4:-NEXT_STAGE_PLAN_2026-02-24.md}"

echo "[1/6] Plan QA"
bash scripts/run_plan_qa.sh "$PLAN_FILE"

echo "[2/6] Documentation audit"
bash scripts/run_doc_audit.sh

echo "[3/6] Model registry check"
bash scripts/check_model_registry.sh

echo "[4/6] Expert QA"
bash scripts/run_expert_qa.sh

echo "[5/6] Auto cycle"
bash scripts/run_auto_cycle.sh "$TARGET_STAGE" "$MAX_ROUNDS" "$SLEEP_SECONDS"

echo "[6/6] Completed next-stage automation pipeline."
