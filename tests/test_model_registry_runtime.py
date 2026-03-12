from __future__ import annotations

import time
import unittest


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
class TestModelRegistryRuntime(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}
        self.reviewer_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_reviewer', 'reviewer')}"}

    def _wait_agent_status(self, task_id: str, expected: set[str], timeout: float = 6.0) -> dict[str, object] | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            response = self.client.get(f"/api/v1/agent/status/{task_id}", headers=self.requester_headers)
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            if payload["status"] in expected:
                return payload
            time.sleep(0.1)
        return None

    def test_task_status_and_events_include_provider_selection(self) -> None:
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "request_text": "운영회의 요약",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "ops sync",
                    "meeting_date": "2026-03-12",
                    "participants": ["Kim"],
                    "notes": "general summary only",
                    "sensitivity": "low",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        payload = response.json()
        task_id = str(payload["task_id"])

        final_payload = self._wait_agent_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        selection = final_payload["provider_selection"]
        self.assertEqual(selection["provider_id"], "api_general")
        self.assertEqual(selection["task_type"], "summarize")

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        selected_events = [item for item in events_response.json()["items"] if item["event_type"] == "MODEL_PROVIDER_SELECTED"]
        self.assertEqual(len(selected_events), 1)
        self.assertEqual(selected_events[0]["provider_id"], "api_general")

    def test_incident_status_and_events_include_provider_selection(self) -> None:
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "incident",
                "request_text": "billing-api 장애 대응",
                "requested_by": "qa_user",
                "metadata": {
                    "service": "billing-api",
                    "severity": "high",
                    "time_window": "15m",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        payload = response.json()
        task_id = str(payload["task_id"])

        final_payload = self._wait_agent_status(task_id, {"NEEDS_HUMAN_APPROVAL"})
        self.assertIsNotNone(final_payload)
        selection = final_payload["provider_selection"]
        self.assertEqual(selection["provider_id"], "local_primary")
        self.assertEqual(selection["task_type"], "incident_response")
        self.assertEqual(selection["sensitivity"], "high")

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        selected_events = [item for item in events_response.json()["items"] if item["event_type"] == "MODEL_PROVIDER_SELECTED"]
        self.assertEqual(len(selected_events), 1)
        self.assertEqual(selected_events[0]["provider_id"], "local_primary")


if __name__ == "__main__":
    unittest.main()
