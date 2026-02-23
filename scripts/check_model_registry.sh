#!/usr/bin/env bash
set -euo pipefail

FILE="configs/model_registry.yaml"
if [[ ! -f "$FILE" ]]; then
  echo "missing $FILE"
  exit 1
fi

check() {
  local pattern="$1"
  local message="$2"
  if rg -q "$pattern" "$FILE"; then
    echo "[PASS] $message"
  else
    echo "[FAIL] $message"
    exit 1
  fi
}

check "^providers:" "providers section exists"
check "id: local_primary" "local provider exists"
check "id: api_general" "api provider exists"
check "^routing_rules:" "routing rules section exists"
check "require_human_approval: true" "approval rule exists"
