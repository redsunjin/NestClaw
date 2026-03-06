from __future__ import annotations

import json
import os
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import issue_dev_jwt
from app.incident_mcp import execute_redmine_action
from app.main import APP


def _requester_headers(actor_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_dev_jwt(actor_id, 'requester')}"}


def _incident_payload(actor_id: str) -> dict[str, object]:
    return {
        "incident_id": f"inc-live-{uuid4().hex[:8]}",
        "service": os.getenv("NEWCLAW_STAGE8_LIVE_INCIDENT_SERVICE", "billing-api"),
        "severity": "low",
        "detected_at": "2026-03-07T00:00:00Z",
        "source": "live_rehearsal",
        "summary": os.getenv(
            "NEWCLAW_STAGE8_LIVE_SUMMARY",
            "internal-only stage8 live rehearsal for sandbox validation",
        ),
        "time_window": "15m",
        "requested_by": actor_id,
        "policy_profile": "default",
        "dry_run": True,
    }


def _wait_for_done(client: TestClient, task_id: str, headers: dict[str, str], timeout: float = 10.0) -> dict[str, object]:
    deadline = time.time() + timeout
    last_payload: dict[str, object] | None = None
    while time.time() < deadline:
        response = client.get(f"/api/v1/incident/status/{task_id}", headers=headers)
        response.raise_for_status()
        payload = response.json()
        last_payload = payload
        if payload["status"] in {"DONE", "NEEDS_HUMAN_APPROVAL", "FAILED_RETRYABLE"}:
            return payload
        time.sleep(0.1)
    raise RuntimeError(f"incident did not complete in time: {last_payload}")


def _extract_issue_ref(events: list[dict[str, object]]) -> str:
    for item in events:
        if item.get("event_type") == "INCIDENT_ACTION_EXECUTED":
            external_ref = str(item.get("external_ref") or "").strip()
            if external_ref:
                return external_ref
    raise RuntimeError("incident create flow did not produce external_ref")


def _normalize_lifecycle_result(method: str, response: dict[str, object]) -> dict[str, object]:
    payload = dict(response.get("response") or {})
    return {
        "method": method,
        "mode": response.get("mode"),
        "status": payload.get("status"),
        "external_ref": payload.get("external_ref"),
        "issue_id": payload.get("issue_id"),
        "message": payload.get("message"),
    }


def main() -> int:
    actor_id = os.getenv("NEWCLAW_STAGE8_LIVE_REQUESTED_BY", "stage8_live_runner")
    assignee = os.getenv("NEWCLAW_STAGE8_SANDBOX_ASSIGNEE", "ops_oncall")
    transition = os.getenv("NEWCLAW_STAGE8_SANDBOX_TRANSITION", "In Progress")
    headers = _requester_headers(actor_id)
    client = TestClient(APP)

    create_response = client.post(
        "/api/v1/incident/create",
        json=_incident_payload(actor_id),
        headers=headers,
    )
    create_response.raise_for_status()
    create_payload = create_response.json()
    task_id = create_payload["task_id"]
    incident_id = create_payload["incident_id"]

    run_response = client.post(
        "/api/v1/incident/run",
        json={
            "task_id": task_id,
            "idempotency_key": f"stage8-live-{uuid4().hex[:10]}",
            "run_mode": "mcp-live",
        },
        headers=headers,
    )
    run_response.raise_for_status()

    final_payload = _wait_for_done(client, task_id, headers)
    if final_payload["status"] != "DONE":
        raise RuntimeError(f"incident live rehearsal did not reach DONE: {final_payload}")

    events_response = client.get(f"/api/v1/incident/events/{task_id}", headers=headers)
    events_response.raise_for_status()
    events_payload = events_response.json()
    issue_ref = _extract_issue_ref(list(events_payload["items"]))

    actor_context = {"actor_id": actor_id, "actor_role": "requester"}
    lifecycle_payloads = [
        (
            "issue.update",
            {
                "issue_id": issue_ref,
                "description": f"Stage 8 live rehearsal update for {incident_id}",
                "summary": "status update from live rehearsal runner",
            },
        ),
        (
            "issue.add_comment",
            {
                "issue_id": issue_ref,
                "comment": f"Stage 8 live rehearsal comment for {incident_id}",
            },
        ),
        (
            "issue.assign",
            {
                "issue_id": issue_ref,
                "assignee": assignee,
            },
        ),
        (
            "issue.transition",
            {
                "issue_id": issue_ref,
                "transition": transition,
            },
        ),
    ]

    lifecycle_results: list[dict[str, object]] = []
    for method, payload in lifecycle_payloads:
        response = execute_redmine_action(
            method,
            payload,
            actor_context,
            dry_run=False,
            timeout_seconds=5.0,
        )
        lifecycle_results.append(_normalize_lifecycle_result(method, response))

    summary = {
        "task_id": task_id,
        "incident_id": incident_id,
        "run_mode": final_payload.get("run_mode"),
        "report_path": final_payload.get("result", {}).get("report_path"),
        "issue_ref": issue_ref,
        "incident_action_results": final_payload.get("result"),
        "lifecycle_results": lifecycle_results,
        "event_count": events_payload.get("count"),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
