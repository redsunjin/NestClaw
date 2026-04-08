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
        self.assertEqual(final_payload["state_summary"]["canonical_state"], "done")
        self.assertIn(final_payload["state_summary"]["canonical_reason_code"], {"completed", "planner_degraded"})
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
        self.assertEqual(final_payload["state_summary"]["canonical_state"], "done")
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

    def test_recent_agent_tasks_filters_for_requester(self) -> None:
        other_headers = {"Authorization": f"Bearer {issue_dev_jwt('other_user', 'requester')}"}

        first = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "qa user task",
                "request_text": "회의 메모를 요약해줘",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "ops sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Kim"],
                    "notes": "내부 메모",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(first.status_code, 202)

        second = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "other user task",
                "request_text": "회의 메모를 요약해줘",
                "requested_by": "other_user",
                "metadata": {
                    "meeting_title": "other sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Lee"],
                    "notes": "다른 메모",
                },
            },
            headers=other_headers,
        )
        self.assertEqual(second.status_code, 202)

        recent_response = self.client.get("/api/v1/agent/recent?limit=10", headers=self.requester_headers)
        self.assertEqual(recent_response.status_code, 200)
        payload = recent_response.json()
        self.assertGreaterEqual(payload["count"], 1)
        requested_bys = {item["requested_by"] for item in payload["items"]}
        self.assertEqual(requested_bys, {"qa_user"})
        self.assertTrue(any(item.get("planning_source") for item in payload["items"]))
        self.assertTrue(any(item.get("planned_tool_ids") for item in payload["items"]))
        self.assertTrue(any((item.get("state_summary") or {}).get("canonical_reason_code") for item in payload["items"]))

    def test_agent_report_preview_and_raw_are_authorized(self) -> None:
        other_headers = {"Authorization": f"Bearer {issue_dev_jwt('other_user', 'requester')}"}
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "report preview task",
                "request_text": "회의 메모를 요약해줘",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "preview sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Kim"],
                    "notes": "preview note",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)

        preview_response = self.client.get(f"/api/v1/agent/report/{task_id}?max_chars=500", headers=self.requester_headers)
        self.assertEqual(preview_response.status_code, 200)
        preview_payload = preview_response.json()
        self.assertEqual(preview_payload["task_id"], task_id)
        self.assertIn("preview note", preview_payload["preview_text"])
        self.assertEqual(preview_payload["report_name"], "report.md")

        raw_response = self.client.get(f"/api/v1/agent/report/{task_id}/raw", headers=self.requester_headers)
        self.assertEqual(raw_response.status_code, 200)
        self.assertIn("text/markdown", raw_response.headers.get("content-type", ""))

        forbidden_response = self.client.get(f"/api/v1/agent/report/{task_id}", headers=other_headers)
        self.assertEqual(forbidden_response.status_code, 403)

    def test_agent_bundle_returns_summary_for_requester_and_detail_for_approver(self) -> None:
        approver_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_approver', 'approver')}"}
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "approval bundle task",
                "request_text": "요약 결과를 외부 전송 해주세요",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "approval sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Kim"],
                    "notes": "요약 결과를 외부 전송 해주세요",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        requester_bundle_response = self.client.get(
            f"/api/v1/agent/bundle/{task_id}?max_chars=500",
            headers=self.requester_headers,
        )
        self.assertEqual(requester_bundle_response.status_code, 200)
        requester_bundle = requester_bundle_response.json()
        self.assertEqual(requester_bundle["approval"]["access_level"], "summary")
        self.assertEqual(requester_bundle["approval"]["actions"], [])
        self.assertFalse(requester_bundle["report"]["available"])
        self.assertEqual(requester_bundle["status"]["state_summary"]["canonical_state"], "approval_pending")
        self.assertEqual(requester_bundle["status"]["state_summary"]["canonical_reason_code"], "policy_blocked")

        approver_bundle_response = self.client.get(
            f"/api/v1/agent/bundle/{task_id}?max_chars=500",
            headers=approver_headers,
        )
        self.assertEqual(approver_bundle_response.status_code, 200)
        approver_bundle = approver_bundle_response.json()
        self.assertEqual(approver_bundle["approval"]["access_level"], "detail")
        self.assertGreaterEqual(approver_bundle["approval"]["action_count"], 0)
        self.assertEqual(approver_bundle["status"]["state_summary"]["canonical_reason_code"], "policy_blocked")

    def test_agent_handoff_packet_returns_completed_summary_for_done_task(self) -> None:
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "handoff complete task",
                "request_text": "주간 운영회의 메모를 요약해줘",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "ops sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Kim"],
                    "notes": "preview note",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]
        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)

        handoff_response = self.client.get(
            f"/api/v1/agent/handoff/{task_id}?max_chars=500",
            headers=self.requester_headers,
        )
        self.assertEqual(handoff_response.status_code, 200)
        payload = handoff_response.json()
        self.assertEqual(payload["packet_version"], "v1")
        self.assertEqual(payload["packet_type"], "completed")
        self.assertEqual(payload["recommended_handoff_owner"], "requester_or_operator")
        self.assertTrue(payload["report"]["available"])
        self.assertIn("NestClaw Operator Handoff Packet", payload["markdown"])
        self.assertIn(task_id, payload["markdown"])

    def test_agent_handoff_packet_preserves_approval_role_gating(self) -> None:
        approver_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_approver', 'approver')}"}
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "handoff approval task",
                "request_text": "요약 결과를 외부 전송 해주세요",
                "requested_by": "qa_user",
                "metadata": {
                    "meeting_title": "approval sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Kim"],
                    "notes": "요약 결과를 외부 전송 해주세요",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        requester_response = self.client.get(
            f"/api/v1/agent/handoff/{task_id}?max_chars=500",
            headers=self.requester_headers,
        )
        self.assertEqual(requester_response.status_code, 200)
        requester_payload = requester_response.json()
        self.assertEqual(requester_payload["packet_type"], "approval_pending")
        self.assertEqual(requester_payload["recommended_handoff_owner"], "approver_admin")
        self.assertEqual(requester_payload["approval"]["access_level"], "summary")
        self.assertEqual(requester_payload["approval"]["actions"], [])

        approver_response = self.client.get(
            f"/api/v1/agent/handoff/{task_id}?max_chars=500",
            headers=approver_headers,
        )
        self.assertEqual(approver_response.status_code, 200)
        approver_payload = approver_response.json()
        self.assertEqual(approver_payload["packet_type"], "approval_pending")
        self.assertEqual(approver_payload["approval"]["access_level"], "detail")

    def test_agent_handoff_packet_classifies_retryable_failure_as_blocked(self) -> None:
        response = self.client.post(
            "/api/v1/agent/submit",
            json={
                "task_kind": "task",
                "title": "handoff blocked task",
                "request_text": "운영 메모를 정리해줘",
                "requested_by": "qa_user",
                "auto_run": False,
                "metadata": {
                    "meeting_title": "blocked sync",
                    "meeting_date": "2026-03-13",
                    "participants": ["Kim"],
                    "notes": "internal only",
                },
            },
            headers=self.requester_headers,
        )
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        with main_module.STORE_LOCK:
            task = main_module.TASKS[task_id]
            main_module._set_status(task, main_module.TaskStatus.FAILED_RETRYABLE, next_action="retry_allowed")
            task["last_error"] = "timeout while sending handoff packet"

        handoff_response = self.client.get(
            f"/api/v1/agent/handoff/{task_id}?max_chars=500",
            headers=self.requester_headers,
        )
        self.assertEqual(handoff_response.status_code, 200)
        payload = handoff_response.json()
        self.assertEqual(payload["packet_type"], "blocked")
        self.assertEqual(payload["operator_summary"]["canonical_state"], "retryable_failure")
        self.assertEqual(payload["operator_summary"]["canonical_reason_code"], "retryable_failure")
        self.assertIn("retryable_failure", payload["markdown"])


if __name__ == "__main__":
    unittest.main()
