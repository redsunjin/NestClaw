#!/usr/bin/env bash
set -u -o pipefail

PASS_EXIT_CODE=0
FAIL_EXIT_CODE=1
SKIP_EXIT_CODE=10

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
REPORT_DIR="reports/qa"
REPORT_FILE="${REPORT_DIR}/idp-rotation-rehearsal-${TS}.md"

pass() {
  echo "[idp-rotation][PASS] $*"
  exit "${PASS_EXIT_CODE}"
}

fail() {
  echo "[idp-rotation][FAIL] $*" >&2
  exit "${FAIL_EXIT_CODE}"
}

skip() {
  echo "[idp-rotation][SKIP] $*" >&2
  exit "${SKIP_EXIT_CODE}"
}

if ! command -v python3 >/dev/null 2>&1; then
  skip "python3 not found on PATH"
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import fastapi  # noqa: F401
PY
then
  skip "fastapi runtime dependency unavailable"
fi

mkdir -p "${REPORT_DIR}"
{
  echo "# IdP Key Rotation Rehearsal Report"
  echo ""
  echo "- executed_at_utc: ${TS}"
  echo ""
  echo "## Checks"
} >"${REPORT_FILE}"

# Always run local regression proof first.
if python3 -m unittest tests.test_auth_idp >/tmp/newclaw_idp_rotation_test.out 2>/tmp/newclaw_idp_rotation_test.err; then
  echo "- [PASS] auth idp unit tests" >>"${REPORT_FILE}"
else
  echo "- [FAIL] auth idp unit tests" >>"${REPORT_FILE}"
  echo "  - stderr: $(tr '\n' ' ' </tmp/newclaw_idp_rotation_test.err)" >>"${REPORT_FILE}"
  fail "unit test failed"
fi

JWKS_PATH="${NEWCLAW_IDP_REHEARSAL_JWKS_PATH:-}"
ISSUER="${NEWCLAW_IDP_REHEARSAL_ISSUER:-}"
AUDIENCE="${NEWCLAW_IDP_REHEARSAL_AUDIENCE:-}"
OLD_TOKEN="${NEWCLAW_IDP_REHEARSAL_OLD_TOKEN:-}"
NEW_TOKEN="${NEWCLAW_IDP_REHEARSAL_NEW_TOKEN:-}"

if [[ -z "${JWKS_PATH}" && -z "${OLD_TOKEN}" && -z "${NEW_TOKEN}" ]]; then
  echo "- [PASS] live token check skipped (unit regression only mode)" >>"${REPORT_FILE}"
  echo "- report: ${REPORT_FILE}" >>"${REPORT_FILE}"
  pass "unit regression rehearsal passed (live token check not requested)"
fi

if [[ -z "${JWKS_PATH}" || -z "${ISSUER}" || -z "${AUDIENCE}" || -z "${OLD_TOKEN}" || -z "${NEW_TOKEN}" ]]; then
  echo "- [FAIL] live token check input incomplete" >>"${REPORT_FILE}"
  fail "set NEWCLAW_IDP_REHEARSAL_JWKS_PATH/ISSUER/AUDIENCE/OLD_TOKEN/NEW_TOKEN for live token rehearsal"
fi

if [[ ! -f "${JWKS_PATH}" ]]; then
  echo "- [FAIL] jwks path missing: ${JWKS_PATH}" >>"${REPORT_FILE}"
  fail "jwks path not found"
fi

if NEWCLAW_IDP_JWKS_PATH="${JWKS_PATH}" \
   NEWCLAW_IDP_ISSUER="${ISSUER}" \
   NEWCLAW_IDP_AUDIENCE="${AUDIENCE}" \
   python3 - <<'PY' >/tmp/newclaw_idp_rotation_live.out 2>/tmp/newclaw_idp_rotation_live.err
import os
from app.auth import resolve_actor_context

old_token = os.environ["NEWCLAW_IDP_REHEARSAL_OLD_TOKEN"]
new_token = os.environ["NEWCLAW_IDP_REHEARSAL_NEW_TOKEN"]

old_rejected = False
try:
    resolve_actor_context(None, None, None, None, None, old_token)
except Exception as exc:
    old_rejected = getattr(exc, "status_code", None) == 401

if not old_rejected:
    raise RuntimeError("old token was not rejected after rotation")

actor = resolve_actor_context(None, None, None, None, None, new_token)
print(f"new_token_subject={actor.actor_id}")
print(f"new_token_role={actor.actor_role}")
PY
then
  echo "- [PASS] live token rotation check (old rejected, new accepted)" >>"${REPORT_FILE}"
else
  echo "- [FAIL] live token rotation check" >>"${REPORT_FILE}"
  echo "  - stderr: $(tr '\n' ' ' </tmp/newclaw_idp_rotation_live.err)" >>"${REPORT_FILE}"
  fail "live token rotation check failed"
fi

echo "- report: ${REPORT_FILE}" >>"${REPORT_FILE}"
pass "idp key rotation rehearsal passed"
