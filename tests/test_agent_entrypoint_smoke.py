from __future__ import annotations

import time
import unittest
from pathlib import Path


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
class TestAgentEntrypointSmoke(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}
        self.reviewer_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_reviewer', 'reviewer')}"}

    def _wait_status(self, task_id: str, expected: set[str], timeout: float = 6.0) -> dict[str, object] | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            response = self.client.get(f"/api/v1/agent/status/{task_id}", headers=self.requester_headers)
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            if payload["status"] in expected:
                return payload
            time.sleep(0.1)
        return None

    def test_submit_routes_meeting_task_and_finishes(self) -> None:
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "주간 운영회의 요약",
                "request_text": "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "주간 운영회의",
                    "meeting_date": "2026-03-11",
                    "participants": ["Kim", "Lee"],
                    "notes": "업무A 진행\n업무B 리스크\n업무C 일정",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["resolved_kind"], "task")
        task_id = payload["task_id"]

        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["resolved_kind"], "task")
        report_path = Path(str(final_payload["result"]["report_path"]))
        self.assertTrue(report_path.is_file())

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        event_types = {item["event_type"] for item in events_response.json()["items"]}
        self.assertIn("AGENT_ROUTED", event_types)
        self.assertIn("TASK_CREATED", event_types)

    def test_submit_auto_routes_incident_and_finishes(self) -> None:
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "auto",
                "request_text": "billing-api 장애 대응용 티켓을 생성하고 온콜이 볼 수 있게 정리해줘",
                "requested_by": "qa_user",
                "metadata": {
                    "service": "billing-api",
                    "severity": "low",
                    "time_window": "15m",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["resolved_kind"], "incident")
        task_id = payload["task_id"]

        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["resolved_kind"], "incident")
        self.assertEqual(final_payload["run_mode"], "dry-run")
        self.assertEqual(final_payload["result"]["actions_executed"], 1)

    def test_agent_status_and_events_cover_direct_task_flow(self) -> None:
        create_response = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "회의요약 생성",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "ops sync",
                    "meeting_date": "2026-03-11",
                    "participants": ["Kim"],
                    "notes": "internal only",
                },
                "requested_by": "qa_user",
            },
            headers=self.requester_headers,
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["task_id"]

        run_response = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "agent-direct-task", "run_mode": "standard"},
            headers=self.requester_headers,
        )
        self.assertEqual(run_response.status_code, 202)

        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["resolved_kind"], "task")

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        self.assertGreaterEqual(events_response.json()["count"], 2)


if __name__ == "__main__":
    unittest.main()
