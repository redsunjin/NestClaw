#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate_stage8_env_handoff.sh [env-file]

If env-file is omitted, the current shell environment is validated.
Exit codes:
  0  required env complete
  20 required env missing or invalid (BLOCKED)
  2  invalid usage / file not found
EOF
}

is_truthy() {
  local value
  value="$(printf "%s" "$1" | tr '[:upper:]' '[:lower:]')"
  [[ "$value" == "1" || "$value" == "true" || "$value" == "yes" || "$value" == "on" ]]
}

is_boolish() {
  local value
  value="$(printf "%s" "$1" | tr '[:upper:]' '[:lower:]')"
  [[ -z "$value" || "$value" == "1" || "$value" == "0" || "$value" == "true" || "$value" == "false" || "$value" == "yes" || "$value" == "no" || "$value" == "on" || "$value" == "off" ]]
}

is_url() {
  [[ "$1" =~ ^https?://.+$ ]]
}

SOURCE_LABEL="current-shell"
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 1 ]]; then
  usage
  exit 2
fi

if [[ $# -eq 1 ]]; then
  ENV_FILE="$1"
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "[ERROR] env file not found: $ENV_FILE" >&2
    exit 2
  fi
  SOURCE_LABEL="$ENV_FILE"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

STATUS="READY"
REQUIRED_READY=0
RECOMMENDED_READY=0
REQUIRED_TOTAL=5
RECOMMENDED_TOTAL=5

print_line() {
  printf "%s\n" "$1"
}

SANDBOX_ENABLED="${NEWCLAW_STAGE8_SANDBOX_ENABLED:-}"
if is_truthy "$SANDBOX_ENABLED"; then
  SANDBOX_ENABLED_STATE="READY"
  REQUIRED_READY=$((REQUIRED_READY + 1))
else
  SANDBOX_ENABLED_STATE="MISSING"
  STATUS="BLOCKED"
fi

SANDBOX_BASE_URL="${NEWCLAW_STAGE8_SANDBOX_BASE_URL:-}"
if is_url "$SANDBOX_BASE_URL"; then
  SANDBOX_BASE_URL_STATE="READY"
  REQUIRED_READY=$((REQUIRED_READY + 1))
else
  SANDBOX_BASE_URL_STATE="MISSING"
  STATUS="BLOCKED"
fi

SANDBOX_PROJECT="${NEWCLAW_STAGE8_SANDBOX_PROJECT:-}"
if [[ -n "$SANDBOX_PROJECT" ]]; then
  SANDBOX_PROJECT_STATE="READY"
  REQUIRED_READY=$((REQUIRED_READY + 1))
else
  SANDBOX_PROJECT_STATE="MISSING"
  STATUS="BLOCKED"
fi

LIVE_ENABLED="${NEWCLAW_STAGE8_LIVE_ENABLED:-}"
if is_truthy "$LIVE_ENABLED"; then
  LIVE_ENABLED_STATE="READY"
  REQUIRED_READY=$((REQUIRED_READY + 1))
else
  LIVE_ENABLED_STATE="MISSING"
  STATUS="BLOCKED"
fi

MCP_ENDPOINT="${NEWCLAW_REDMINE_MCP_ENDPOINT:-}"
if is_url "$MCP_ENDPOINT"; then
  MCP_ENDPOINT_STATE="READY"
  REQUIRED_READY=$((REQUIRED_READY + 1))
else
  MCP_ENDPOINT_STATE="MISSING"
  STATUS="BLOCKED"
fi

TOKEN="${NEWCLAW_REDMINE_MCP_TOKEN:-}"
if [[ -n "$TOKEN" ]]; then
  TOKEN_STATE="CONFIGURED"
  RECOMMENDED_READY=$((RECOMMENDED_READY + 1))
else
  TOKEN_STATE="OPTIONAL"
fi

VERIFY_TLS="${NEWCLAW_REDMINE_MCP_VERIFY_TLS:-}"
if is_boolish "$VERIFY_TLS"; then
  if [[ -n "$VERIFY_TLS" ]]; then
    VERIFY_TLS_STATE="CONFIGURED"
    RECOMMENDED_READY=$((RECOMMENDED_READY + 1))
  else
    VERIFY_TLS_STATE="OPTIONAL"
  fi
else
  VERIFY_TLS_STATE="OPTIONAL"
fi

ASSIGNEE="${NEWCLAW_STAGE8_SANDBOX_ASSIGNEE:-}"
if [[ -n "$ASSIGNEE" ]]; then
  ASSIGNEE_STATE="CONFIGURED"
  RECOMMENDED_READY=$((RECOMMENDED_READY + 1))
else
  ASSIGNEE_STATE="OPTIONAL"
fi

TRANSITION="${NEWCLAW_STAGE8_SANDBOX_TRANSITION:-}"
if [[ -n "$TRANSITION" ]]; then
  TRANSITION_STATE="CONFIGURED"
  RECOMMENDED_READY=$((RECOMMENDED_READY + 1))
else
  TRANSITION_STATE="OPTIONAL"
fi

REQUESTED_BY="${NEWCLAW_STAGE8_LIVE_REQUESTED_BY:-}"
if [[ -n "$REQUESTED_BY" ]]; then
  REQUESTED_BY_STATE="CONFIGURED"
  RECOMMENDED_READY=$((RECOMMENDED_READY + 1))
else
  REQUESTED_BY_STATE="OPTIONAL"
fi

print_line ""
print_line "# Stage 8 External Env Validation"
print_line ""
print_line "- source: ${SOURCE_LABEL}"
print_line "- required_ready: ${REQUIRED_READY}/${REQUIRED_TOTAL}"
print_line "- recommended_configured: ${RECOMMENDED_READY}/${RECOMMENDED_TOTAL}"
print_line ""
print_line "## Required Env"

# Re-print in stable order after summary.
if is_truthy "${NEWCLAW_STAGE8_SANDBOX_ENABLED:-}"; then
  print_line "- [READY] NEWCLAW_STAGE8_SANDBOX_ENABLED"
else
  print_line "- [MISSING] NEWCLAW_STAGE8_SANDBOX_ENABLED"
  print_line "  - reason: truthy enable flag required"
fi
if is_url "${NEWCLAW_STAGE8_SANDBOX_BASE_URL:-}"; then
  print_line "- [READY] NEWCLAW_STAGE8_SANDBOX_BASE_URL"
else
  print_line "- [MISSING] NEWCLAW_STAGE8_SANDBOX_BASE_URL"
  print_line "  - reason: http(s) sandbox base URL required"
fi
if [[ -n "${NEWCLAW_STAGE8_SANDBOX_PROJECT:-}" ]]; then
  print_line "- [READY] NEWCLAW_STAGE8_SANDBOX_PROJECT"
else
  print_line "- [MISSING] NEWCLAW_STAGE8_SANDBOX_PROJECT"
  print_line "  - reason: sandbox project key required"
fi
if is_truthy "${NEWCLAW_STAGE8_LIVE_ENABLED:-}"; then
  print_line "- [READY] NEWCLAW_STAGE8_LIVE_ENABLED"
else
  print_line "- [MISSING] NEWCLAW_STAGE8_LIVE_ENABLED"
  print_line "  - reason: truthy live enable flag required"
fi
if is_url "${NEWCLAW_REDMINE_MCP_ENDPOINT:-}"; then
  print_line "- [READY] NEWCLAW_REDMINE_MCP_ENDPOINT"
else
  print_line "- [MISSING] NEWCLAW_REDMINE_MCP_ENDPOINT"
  print_line "  - reason: http(s) MCP endpoint required"
fi

print_line ""
print_line "## Recommended Env"
if [[ "$TOKEN_STATE" == "CONFIGURED" ]]; then
  print_line "- [CONFIGURED] NEWCLAW_REDMINE_MCP_TOKEN"
else
  print_line "- [OPTIONAL] NEWCLAW_REDMINE_MCP_TOKEN"
  print_line "  - note: inject secret at runtime; keep repo copy empty"
fi
if [[ "$VERIFY_TLS_STATE" == "CONFIGURED" ]]; then
  print_line "- [CONFIGURED] NEWCLAW_REDMINE_MCP_VERIFY_TLS"
else
  print_line "- [OPTIONAL] NEWCLAW_REDMINE_MCP_VERIFY_TLS"
  print_line "  - note: runtime default allowed, explicit boolean-like value preferred"
fi
if [[ "$ASSIGNEE_STATE" == "CONFIGURED" ]]; then
  print_line "- [CONFIGURED] NEWCLAW_STAGE8_SANDBOX_ASSIGNEE"
else
  print_line "- [OPTIONAL] NEWCLAW_STAGE8_SANDBOX_ASSIGNEE"
  print_line "  - note: live rehearsal can fall back to runtime default"
fi
if [[ "$TRANSITION_STATE" == "CONFIGURED" ]]; then
  print_line "- [CONFIGURED] NEWCLAW_STAGE8_SANDBOX_TRANSITION"
else
  print_line "- [OPTIONAL] NEWCLAW_STAGE8_SANDBOX_TRANSITION"
  print_line "  - note: live rehearsal can fall back to runtime default"
fi
if [[ "$REQUESTED_BY_STATE" == "CONFIGURED" ]]; then
  print_line "- [CONFIGURED] NEWCLAW_STAGE8_LIVE_REQUESTED_BY"
else
  print_line "- [OPTIONAL] NEWCLAW_STAGE8_LIVE_REQUESTED_BY"
  print_line "  - note: operator trace hint only"
fi

print_line ""
print_line "## Summary"
print_line "- status: ${STATUS}"
if [[ "$STATUS" == "READY" ]]; then
  print_line "- next_action: source the env file in the QA worktree and run bash scripts/run_stage8_readiness_bundle.sh"
  exit 0
fi
print_line "- next_action: complete the missing required env values before rerunning readiness"
exit 20
