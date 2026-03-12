from __future__ import annotations

import time
import unittest
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
class TestToolRegistryRuntime(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}

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

    def test_tools_api_lists_and_gets_catalog_entries(self) -> None:
        list_response = self.client.get("/api/v1/tools", headers=self.requester_headers)
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertGreaterEqual(list_payload["count"], 6)
        tool_ids = {item["tool_id"] for item in list_payload["items"]}
        self.assertIn("internal.summary.generate", tool_ids)
        self.assertIn("redmine.issue.create", tool_ids)
        self.assertIn("slack.message.send", tool_ids)

        detail_response = self.client.get("/api/v1/tools/redmine.issue.create", headers=self.requester_headers)
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()
        self.assertEqual(detail_payload["method"], "issue.create")
        self.assertEqual(detail_payload["adapter"], "redmine_mcp")

    def test_incident_runtime_uses_registered_tool_metadata(self) -> None:
        create_response = self.client.post(
            "/api/v1/incident/create",
            json={
                "incident_id": f"inc-{uuid4().hex[:8]}",
                "service": "billing-api",
                "severity": "low",
                "detected_at": "2026-03-12T12:00:00Z",
                "source": "monitoring",
                "summary": "billing latency increased but remains internal only",
                "time_window": "15m",
                "requested_by": "qa_user",
                "policy_profile": "default",
                "dry_run": True,
            },
            headers=self.requester_headers,
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["task_id"]

        run_response = self.client.post(
            "/api/v1/incident/run",
            json={"task_id": task_id, "idempotency_key": f"tool-runtime-{uuid4().hex[:10]}", "run_mode": "dry-run"},
            headers=self.requester_headers,
        )
        self.assertEqual(run_response.status_code, 202)
        self.assertIsNotNone(self._wait_incident_status(task_id, {"DONE"}))

        with main_module.STORE_LOCK:
            task = dict(main_module.TASKS[task_id])
        action_cards = list(task.get("action_cards") or [])
        planned_actions = list(task.get("planned_actions") or [])
        self.assertEqual(len(action_cards), 1)
        self.assertEqual(len(planned_actions), 1)
        self.assertEqual(action_cards[0]["tool_id"], "redmine.issue.create")
        self.assertEqual(action_cards[0]["tool_family"], "ticketing")
        self.assertEqual(action_cards[0]["execution_call"]["adapter"], "redmine_mcp")
        self.assertEqual(action_cards[0]["execution_call"]["method"], "issue.create")
        self.assertEqual(action_cards[0]["mcp_call"]["adapter"], "redmine_mcp")
        self.assertEqual(action_cards[0]["mcp_call"]["method"], "issue.create")
        self.assertEqual(planned_actions[0]["tool_id"], "redmine.issue.create")

    def test_incident_runtime_plans_slack_notification_when_channel_is_present(self) -> None:
        create_response = self.client.post(
            "/api/v1/incident/create",
            json={
                "incident_id": f"inc-{uuid4().hex[:8]}",
                "service": "billing-api",
                "severity": "low",
                "detected_at": "2026-03-12T12:00:00Z",
                "source": "monitoring",
                "summary": "billing latency increased but remains internal only",
                "time_window": "15m",
                "requested_by": "qa_user",
                "policy_profile": "default",
                "dry_run": True,
                "notify_channel": "#ops-alerts",
            },
            headers=self.requester_headers,
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["task_id"]

        run_response = self.client.post(
            "/api/v1/incident/run",
            json={"task_id": task_id, "idempotency_key": f"tool-slack-{uuid4().hex[:10]}", "run_mode": "dry-run"},
            headers=self.requester_headers,
        )
        self.assertEqual(run_response.status_code, 202)
        final_payload = self._wait_incident_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["result"]["actions_executed"], 2)

        with main_module.STORE_LOCK:
            task = dict(main_module.TASKS[task_id])
        planned_actions = list(task.get("planned_actions") or [])
        tool_ids = [item["tool_id"] for item in planned_actions]
        self.assertEqual(tool_ids, ["redmine.issue.create", "slack.message.send"])
        self.assertEqual(planned_actions[1]["execution_call"]["adapter"], "slack_api")


if __name__ == "__main__":
    unittest.main()
