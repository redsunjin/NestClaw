#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
WORK_DIR="${NEWCLAW_STAGE12_LOCAL_LLM_ONBOARDING_WORK_DIR:-reports/stage12-local-llm-onboarding-smoke/${STAMP}}"
mkdir -p "$WORK_DIR"

python3 scripts/validate_stage12_llm_harness.py --strict-warnings >"$WORK_DIR/validator.txt"

python3 - "$WORK_DIR" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

from app.stage12_jobs import job_describe_payload, job_list_payload

work_dir = Path(sys.argv[1])
profiles = json.loads(Path("configs/agent_profiles.json").read_text(encoding="utf-8"))["profiles"]
profile = next((item for item in profiles if item.get("profile_id") == "local_ollama_ops"), None)
if profile is None:
    raise SystemExit("local_ollama_ops profile missing")
if profile.get("provider_id") != "local_primary":
    raise SystemExit("local_ollama_ops must use local_primary provider")
if profile.get("provider_class") != "local_llm":
    raise SystemExit("local_ollama_ops must be local_llm")
if profile.get("sensitivity_boundary", {}).get("external_send_policy") != "deny":
    raise SystemExit("local_ollama_ops external send must be denied")
if profile.get("execution_budget", {}).get("allow_network") is not False:
    raise SystemExit("local_ollama_ops execution budget must deny network")

model_registry = Path("configs/model_registry.yaml").read_text(encoding="utf-8")
if "id: local_primary" not in model_registry or "engine: ollama" not in model_registry:
    raise SystemExit("model registry must expose local_primary Ollama provider")

listing = job_list_payload(profile_id="local_ollama_ops")
compatible = {item["template_id"] for item in listing["items"] if "local_ollama_ops" in item["compatible_profile_ids"]}
expected = {"daily_status_digest", "issue_triage", "readiness_check"}
if expected - compatible:
    raise SystemExit(f"local_ollama_ops missing compatible templates: {sorted(expected - compatible)}")

describe = job_describe_payload(template_id="readiness_check", profile_id="local_ollama_ops")
compatibility = describe["template"]["profile_compatibility"][0]
if compatibility.get("provider_class") != "local_llm":
    raise SystemExit("readiness_check describe must resolve local_llm for local_ollama_ops")

(work_dir / "job-list-local-ollama.json").write_text(
    json.dumps(listing, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
(work_dir / "job-describe-readiness-local-ollama.json").write_text(
    json.dumps(describe, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

RUN_OUTPUT="$WORK_DIR/readiness-run.json"
python3 -m app.cli job run \
  --template readiness_check \
  --profile local_ollama_ops \
  --input-file examples/stage12_scheduler/readiness-input.json \
  --requested-by stage12_local_llm_onboarding_smoke \
  --actor-id stage12_local_llm_onboarding_smoke \
  --actor-role requester \
  --idempotency-key "stage12:readiness_check:local-ollama-onboarding:${STAMP}" \
  --include-handoff \
  --max-chars 2400 \
  --json >"$RUN_OUTPUT"

python3 - "$RUN_OUTPUT" "$WORK_DIR" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

run_path = Path(sys.argv[1])
work_dir = Path(sys.argv[2])
payload = json.loads(run_path.read_text(encoding="utf-8"))
invocation = payload.get("job_invocation") or {}
status = payload.get("status") or {}
if invocation.get("profile_id") != "local_ollama_ops":
    raise SystemExit("run did not use local_ollama_ops")
if invocation.get("provider_id") != "local_primary":
    raise SystemExit("run did not resolve local_primary provider")
if invocation.get("provider_class") != "local_llm":
    raise SystemExit("run did not resolve local_llm provider class")
if status.get("status") != "DONE":
    raise SystemExit(f"readiness run should be DONE, got {status.get('status')}")
summary = {
    "surface": "stage12.local_llm_onboarding_smoke",
    "profile_id": invocation.get("profile_id"),
    "provider_id": invocation.get("provider_id"),
    "provider_class": invocation.get("provider_class"),
    "task_id": status.get("task_id"),
    "status": status.get("status"),
    "work_dir": str(work_dir),
}
(work_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    "[OK] stage12 local llm onboarding smoke "
    f"profile={summary['profile_id']} "
    f"provider={summary['provider_id']} "
    f"task_id={summary['task_id']} "
    f"work_dir={work_dir}"
)
PY

if [[ "${NEWCLAW_STAGE12_OLLAMA_LIVE_CHECK:-0}" == "1" ]]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "[SKIP] ollama command is not installed" >&2
    exit 10
  fi
  ollama list >"$WORK_DIR/ollama-list.txt"
fi
