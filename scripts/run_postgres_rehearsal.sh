#!/usr/bin/env bash
set -u -o pipefail

PASS_EXIT_CODE=0
FAIL_EXIT_CODE=1
SKIP_EXIT_CODE=10

DATABASE_URL="${NEWCLAW_DATABASE_URL:-${1:-}}"

pass() {
  echo "[postgres-rehearsal][PASS] $*"
  exit "${PASS_EXIT_CODE}"
}

fail() {
  echo "[postgres-rehearsal][FAIL] $*" >&2
  exit "${FAIL_EXIT_CODE}"
}

skip() {
  echo "[postgres-rehearsal][SKIP] $*" >&2
  exit "${SKIP_EXIT_CODE}"
}

if [[ -z "${DATABASE_URL}" ]]; then
  skip "NEWCLAW_DATABASE_URL is not set"
fi

if ! command -v python3 >/dev/null 2>&1; then
  skip "python3 not found on PATH"
fi

if ! command -v psql >/dev/null 2>&1; then
  skip "psql command not found on PATH"
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import fastapi  # noqa: F401
import uvicorn  # noqa: F401
import psycopg  # noqa: F401
PY
then
  skip "python runtime dependencies unavailable (fastapi/uvicorn/psycopg)"
fi

if ! bash scripts/migrate_postgres.sh up "${DATABASE_URL}" >/tmp/newclaw_postgres_rehearsal_migrate.out 2>/tmp/newclaw_postgres_rehearsal_migrate.err; then
  fail "migration failed: $(tr '\n' ' ' </tmp/newclaw_postgres_rehearsal_migrate.err)"
fi

if ! NEWCLAW_DB_BACKEND=postgres NEWCLAW_DATABASE_URL="${DATABASE_URL}" python3 - <<'PY' >/tmp/newclaw_postgres_rehearsal_run.out 2>/tmp/newclaw_postgres_rehearsal_run.err
from __future__ import annotations

import importlib
import time

from fastapi.testclient import TestClient

from app.auth import issue_dev_jwt
import app.main as main_mod


def wait_status(client: TestClient, task_id: str, headers: dict[str, str], expected: set[str], timeout: float = 5.0) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/v1/task/status/{task_id}", headers=headers)
        if resp.status_code == 200:
            payload = resp.json()
            if payload["status"] in expected:
                return payload
        time.sleep(0.1)
    return None


client = TestClient(main_mod.APP)
headers = {"Authorization": f"Bearer {issue_dev_jwt('pg_rehearsal_user', 'requester')}"}

create_resp = client.post(
    "/api/v1/task/create",
    json={
        "title": "postgres rehearsal",
        "template_type": "meeting_summary",
        "input": {
            "meeting_title": "postgres rehearsal",
            "meeting_date": "2026-02-24",
            "participants": ["ops"],
            "notes": "postgres persistence check",
        },
        "requested_by": "pg_rehearsal_user",
    },
    headers=headers,
)
assert create_resp.status_code == 201, create_resp.text
task_id = create_resp.json()["task_id"]

run_resp = client.post(
    "/api/v1/task/run",
    json={"task_id": task_id, "idempotency_key": "pg_rehearsal_1", "run_mode": "standard"},
    headers=headers,
)
assert run_resp.status_code == 202, run_resp.text

status_payload = wait_status(client, task_id, headers, {"DONE", "NEEDS_HUMAN_APPROVAL"})
assert status_payload is not None, "task status did not converge"

main_mod = importlib.reload(main_mod)
client_after_reload = TestClient(main_mod.APP)
status_after_reload = client_after_reload.get(f"/api/v1/task/status/{task_id}", headers=headers)
assert status_after_reload.status_code == 200, status_after_reload.text
payload_after_reload = status_after_reload.json()
assert payload_after_reload["task_id"] == task_id
assert payload_after_reload["status"] in {"DONE", "NEEDS_HUMAN_APPROVAL"}
print(f"persisted_task_id={task_id}")
print(f"persisted_status={payload_after_reload['status']}")
PY
then
  fail "runtime rehearsal failed: $(tr '\n' ' ' </tmp/newclaw_postgres_rehearsal_run.err)"
fi

pass "postgres persistence rehearsal passed"
