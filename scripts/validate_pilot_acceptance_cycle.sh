#!/usr/bin/env bash
set -euo pipefail

ACCEPTANCE_DOC="${1:-NESTCLAW_PILOT_ACCEPTANCE_CYCLE_2026-04-10.md}"
GO_NO_GO_DOC="NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md"
EVIDENCE_DOC="NESTCLAW_PILOT_EVIDENCE_MATRIX_2026-04-05.md"
ENV_HANDOFF_DOC="STAGE8_EXTERNAL_ENV_HANDOFF_PROFILE_2026-04-05.md"
RUNBOOK_DOC="STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md"
RERUN_DOC="STAGE8_QA_RERUN_STATUS_2026-04-05.md"
HANDOFF_SPEC="NESTCLAW_OPERATOR_HANDOFF_PACKET_SPEC.md"

fail() {
  echo "[pilot-acceptance][FAIL] $1"
  exit 1
}

require_file() {
  local file="$1"
  [[ -f "$file" ]] || fail "missing file: $file"
}

require_pattern() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  rg -q "$pattern" "$file" || fail "missing ${label} in ${file}"
}

for file in "$ACCEPTANCE_DOC" "$GO_NO_GO_DOC" "$EVIDENCE_DOC" "$ENV_HANDOFF_DOC" "$RUNBOOK_DOC" "$RERUN_DOC" "$HANDOFF_SPEC"; do
  require_file "$file"
done

require_pattern "$ACCEPTANCE_DOC" 'Conditional Go' 'conditional go rule'
require_pattern "$ACCEPTANCE_DOC" 'OPERATIONAL_HOLD|operational hold' 'operational hold rule'
require_pattern "$ACCEPTANCE_DOC" 'BLOCKED' 'blocked rule'
require_pattern "$ACCEPTANCE_DOC" 'FAIL' 'fail rule'
require_pattern "$ACCEPTANCE_DOC" 'agent\.handoff' 'handoff packet reference'
require_pattern "$GO_NO_GO_DOC" 'NO-GO for external live pilot' 'current pilot recommendation'
require_pattern "$EVIDENCE_DOC" 'NO-GO' 'evidence matrix pilot snapshot'
require_pattern "$RERUN_DOC" 'current_readiness_status: `BLOCKED`' 'blocked readiness snapshot'
require_pattern "$ENV_HANDOFF_DOC" 'NEWCLAW_STAGE8_SANDBOX_ENABLED' 'required external env'
require_pattern "$RUNBOOK_DOC" 'Decision Handling' 'resume decision handling'
require_pattern "$HANDOFF_SPEC" 'packet_type' 'handoff packet field'

current_decision="$(sed -n 's/^- 현재 권고: `\(.*\)`/\1/p' "$GO_NO_GO_DOC" | head -n 1)"
current_readiness="$(sed -n 's/^- current_readiness_status: `\(.*\)`/\1/p' "$RERUN_DOC" | head -n 1)"

cat <<EOF
# NestClaw Pilot Acceptance Cycle Validation
- acceptance_cycle_doc: ${ACCEPTANCE_DOC}
- current_pilot_decision: ${current_decision:-unknown}
- current_readiness_state: ${current_readiness:-unknown}
- required_inputs: operator handoff packet, env handoff profile, evidence matrix, runbook, latest readiness summary
- taxonomy: BLOCKED / FAIL / OPERATIONAL_HOLD
- status: READY
EOF
