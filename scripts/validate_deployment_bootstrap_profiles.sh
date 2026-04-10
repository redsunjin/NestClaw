#!/usr/bin/env bash
set -euo pipefail

PROFILE_PATH="${1:-configs/deployment_bootstrap_profiles.json}"

if [[ ! -f "$PROFILE_PATH" ]]; then
  echo "[ERROR] profile file not found: $PROFILE_PATH" >&2
  exit 2
fi

python3 - "$PROFILE_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
profiles = payload.get("profiles")
if not isinstance(profiles, list) or len(profiles) < 3:
    raise SystemExit("[FAIL] expected at least three deployment profiles")

required_ids = {"local_dev", "operator_sidecar", "upper_agent_host"}
seen_ids = set()

for item in profiles:
    profile_id = str(item.get("profile_id") or "").strip()
    if not profile_id:
        raise SystemExit("[FAIL] profile_id is required")
    seen_ids.add(profile_id)

    http = dict(item.get("http") or {})
    mcp = dict(item.get("mcp") or {})
    auth = dict(item.get("auth") or {})
    restart = dict(item.get("restart_policy") or {})

    http_command = str(http.get("command") or "")
    mcp_command = str(mcp.get("command") or "")
    health_url = str(http.get("health_url") or "")
    recommended_mode = str(auth.get("recommended_mode") or "")
    default_role = str(auth.get("default_actor_role") or "")

    if "uvicorn app.main:APP" not in http_command:
        raise SystemExit(f"[FAIL] http command missing uvicorn baseline: {profile_id}")
    if "python3 app/mcp_server.py" not in mcp_command:
        raise SystemExit(f"[FAIL] mcp command missing stdio baseline: {profile_id}")
    if not health_url.endswith("/health"):
        raise SystemExit(f"[FAIL] health URL must end with /health: {profile_id}")
    if str(mcp.get("transport") or "") != "stdio":
        raise SystemExit(f"[FAIL] mcp transport must be stdio: {profile_id}")
    if recommended_mode not in {"jwt_local", "jwt_idp", "trusted_sso_headers"}:
        raise SystemExit(f"[FAIL] unsupported auth mode: {profile_id} -> {recommended_mode}")
    if default_role not in {"requester", "reviewer"}:
        raise SystemExit(f"[FAIL] default actor role must stay low-privilege: {profile_id} -> {default_role}")
    if not restart.get("http") or not restart.get("mcp"):
        raise SystemExit(f"[FAIL] restart policy missing: {profile_id}")
    readiness_sequence = mcp.get("readiness_sequence") or []
    expected_sequence = ["initialize", "notifications/initialized", "tools/list", "catalog.manifest"]
    if readiness_sequence != expected_sequence:
        raise SystemExit(f"[FAIL] unexpected readiness sequence: {profile_id}")

missing = required_ids - seen_ids
if missing:
    raise SystemExit(f"[FAIL] missing deployment profiles: {sorted(missing)}")

print("# NestClaw Deployment Bootstrap Profile Validation")
print(f"- source: {path}")
print(f"- profile_count: {len(profiles)}")
for item in profiles:
    print(
        f"- {item['profile_id']}: http_required={item['http']['required']} "
        f"mcp_required={item['mcp']['required']} auth={item['auth']['recommended_mode']}"
    )
print("- status: READY")
PY
