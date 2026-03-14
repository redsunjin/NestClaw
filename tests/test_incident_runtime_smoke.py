from __future__ import annotations

import time
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4


try:
    from fastapi.testclient import TestClient
    from app.auth import issue_dev_jwt
    from app.main import APP
    from app import main as main_module
    from tests.runtime_test_utils import reset_runtime_state
except Exception as exc:  # pragma: no cover - environment dependent
    TestClient = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(TestClient is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestIncidentRuntimeSmoke(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}
        self.reviewer_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_reviewer', 'reviewer')}"}
        self.approver_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_approver', 'approver')}"}

    def _incident_payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "incident_id": f"inc-{uuid4().hex[:8]}",
            "service": "billing-api",
            "severity": "low",
            "detected_at": "2026-03-06T01:00:00Z",
            "source": "monitoring",
            "summary": "billing latency increased but remains internal only",
            "time_window": "15m",
            "requested_by": "qa_user",
            "policy_profile": "default",
            "dry_run": True,
        }
        payload.update(overrides)
        return payload

    def _create_incident(self, **overrides: object) -> str:
        response = self.client.post(
            "/api/v1/incident/create",
            json=self._incident_payload(**overrides),
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["status"], "READY")
        return payload["task_id"]

    def _run_incident(self, task_id: str, *, run_mode: str = "dry-run") -> dict[str, object]:
        response = self.client.post(
            "/api/v1/incident/run",
            json={
                "task_id": task_id,
                "idempotency_key": f"incident-smoke-{uuid4().hex[:10]}",
                "run_mode": run_mode,
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        return response.json()

    def _wait_incident_status(self, task_id: str, expected: set[str], timeout: float = 6.0) -> dict[str, object] | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            response = self.client.get(f"/api/v1/incident/status/{task_id}", headers=self.requester_headers)
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            if payload["status"] in expected:
                return payload
            time.sleep(0.1)
        return None

    def test_incident_done_flow_generates_report_and_events(self) -> None:
        task_id = self._create_incident()
        self._run_incident(task_id)

        final_payload = self._wait_incident_status(task_id, {"DONE"})

        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["status"], "DONE")
        self.assertEqual(final_payload["planning_provenance"]["source"], "deterministic_incident_planner")
        self.assertFalse(final_payload["planning_provenance"]["degraded_mode"])
        self.assertIn(
            "redmine.issue.create",
            [item["tool_id"] for item in final_payload["planning_provenance"]["eligible_tools"] if item["eligible"]],
        )
        result = final_payload["result"]
        self.assertEqual(result["actions_executed"], 1)
        self.assertEqual(result["remaining_risk"], "human_review_recommended")
        report_path = Path(result["report_path"])
        self.assertTrue(report_path.is_file())
        self.assertEqual(report_path.name, "incident_report.md")

        with main_module.STORE_LOCK:
            task = dict(main_module.TASKS[task_id])
        action_cards = list(task.get("action_cards") or [])
        planned_actions = list(task.get("planned_actions") or [])
        action_results = list(task.get("action_results") or [])
        self.assertEqual(action_cards[0]["tool_id"], "redmine.issue.create")
        self.assertEqual(planned_actions[0]["tool_id"], "redmine.issue.create")
        self.assertEqual(planned_actions[0]["execution_call"]["adapter"], "redmine_mcp")
        self.assertEqual(action_cards[0]["mcp_call"]["adapter"], "redmine_mcp")
        self.assertEqual(action_results[0]["tool_id"], "redmine.issue.create")

        events_response = self.client.get(f"/api/v1/incident/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        events_payload = events_response.json()
        event_types = {item["event_type"] for item in events_payload["items"]}
        self.assertIn("INCIDENT_CREATED", event_types)
        self.assertIn("INCIDENT_CONTEXT_BUILT", event_types)
        self.assertIn("INCIDENT_PLAN_GENERATED", event_types)
        self.assertIn("INCIDENT_ACTION_EXECUTED", event_types)
        self.assertIn("PLANNED_ACTION_EXECUTED", event_types)
        executed_events = [item for item in events_payload["items"] if item["event_type"] == "INCIDENT_ACTION_EXECUTED"]
        self.assertEqual(executed_events[0]["tool_id"], "redmine.issue.create")

    def test_high_risk_incident_requires_approval_then_resumes(self) -> None:
        task_id = self._create_incident(severity="high", summary="customer-facing outage requires on-call coordination")
        self._run_incident(task_id)

        approval_payload = self._wait_incident_status(task_id, {"NEEDS_HUMAN_APPROVAL"})

        self.assertIsNotNone(approval_payload)
        self.assertEqual(approval_payload["planning_provenance"]["source"], "deterministic_incident_planner")
        self.assertEqual(approval_payload["approval_reason"], "high_risk_action")
        queue_id = approval_payload["approval_queue_id"]

        approve_response = self.client.post(
            f"/api/v1/approvals/{queue_id}/approve",
            json={"acted_by": "qa_approver", "comment": "approved for dry-run incident orchestration"},
            headers=self.approver_headers,
        )
        self.assertEqual(approve_response.status_code, 200)

        final_payload = self._wait_incident_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["status"], "DONE")
        self.assertEqual(final_payload["result"]["actions_executed"], 1)

    def test_policy_block_incident_routes_to_approval(self) -> None:
        task_id = self._create_incident(summary="Please external send the incident summary to a partner channel")
        self._run_incident(task_id)

        approval_payload = self._wait_incident_status(task_id, {"NEEDS_HUMAN_APPROVAL"})

        self.assertIsNotNone(approval_payload)
        self.assertEqual(approval_payload["approval_reason"], "external_send_requested")

        events_response = self.client.get(f"/api/v1/incident/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        event_types = {item["event_type"] for item in events_response.json()["items"]}
        self.assertIn("BLOCKED_POLICY", event_types)

    def test_retry_exhausted_incident_routes_to_approval(self) -> None:
        task_id = self._create_incident(source="simulate_mcp_timeout")
        self._run_incident(task_id)

        approval_payload = self._wait_incident_status(task_id, {"NEEDS_HUMAN_APPROVAL"}, timeout=8.0)

        self.assertIsNotNone(approval_payload)
        self.assertEqual(approval_payload["approval_reason"], "retry_exhausted")

        events_response = self.client.get(f"/api/v1/incident/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        event_types = [item["event_type"] for item in events_response.json()["items"]]
        self.assertIn("RETRY_STARTED", event_types)

    def test_mcp_live_mode_keeps_rag_dry_run_and_executes_live_adapter(self) -> None:
        task_id = self._create_incident()
        captured: dict[str, object] = {}

        def fake_redmine_action(
            method: str,
            payload: dict[str, object],
            actor_context: dict[str, object],
            *,
            dry_run: bool | None = None,
            timeout_seconds: float | None = None,
        ) -> dict[str, object]:
            captured["method"] = method
            captured["payload"] = dict(payload)
            captured["dry_run"] = dry_run
            captured["actor_context"] = dict(actor_context)
            captured["timeout_seconds"] = timeout_seconds
            return {
                "provider": "redmine_mcp",
                "mode": "live",
                "executed": True,
                "method": method,
                "timeout_seconds": timeout_seconds,
                "actor_id": actor_context["actor_id"],
                "actor_role": actor_context["actor_role"],
                "request_payload": dict(payload),
                "response": {
                    "status": "ok",
                    "external_ref": "RM-LIVE-001",
                },
                "generated_at": "2026-03-07T00:00:00+00:00",
            }

        with patch.dict(main_module.INCIDENT_ADAPTERS, {"redmine_mcp": fake_redmine_action}, clear=False):
            self._run_incident(task_id, run_mode="mcp-live")
            final_payload = self._wait_incident_status(task_id, {"DONE"})

        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["status"], "DONE")
        self.assertEqual(final_payload["run_mode"], "mcp-live")
        self.assertFalse(captured["dry_run"])
        self.assertEqual(captured["method"], "issue.create")
        self.assertEqual(captured["actor_context"]["actor_id"], "qa_user")

        report_path = Path(final_payload["result"]["report_path"])
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("- run_mode: mcp-live", report_text)
        self.assertIn("- context_dry_run: True", report_text)
        self.assertIn("- mcp_dry_run: False", report_text)

        events_response = self.client.get(f"/api/v1/incident/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        executed_events = [
            item for item in events_response.json()["items"] if item["event_type"] == "INCIDENT_ACTION_EXECUTED"
        ]
        self.assertEqual(len(executed_events), 1)
        self.assertEqual(executed_events[0]["mode"], "live")

    def test_task_and_incident_routes_are_isolated(self) -> None:
        incident_task_id = self._create_incident()

        task_status_response = self.client.get(
            f"/api/v1/task/status/{incident_task_id}",
            headers=self.requester_headers,
        )
        self.assertEqual(task_status_response.status_code, 404)
        self.assertEqual(task_status_response.json()["detail"]["error"]["code"], "TASK_NOT_FOUND")

        task_create_response = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "meeting summary",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "ops sync",
                    "meeting_date": "2026-03-06",
                    "participants": ["Kim"],
                    "notes": "internal only",
                },
                "requested_by": "qa_user",
            },
            headers=self.requester_headers,
        )
        self.assertEqual(task_create_response.status_code, 201)
        task_id = task_create_response.json()["task_id"]

        incident_status_response = self.client.get(
            f"/api/v1/incident/status/{task_id}",
            headers=self.requester_headers,
        )
        self.assertEqual(incident_status_response.status_code, 404)
        self.assertEqual(incident_status_response.json()["detail"]["error"]["code"], "INCIDENT_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
