from __future__ import annotations

import time
import unittest


try:
    from fastapi.testclient import TestClient
    from app.main import APP
except Exception as exc:  # pragma: no cover - environment dependent
    TestClient = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(TestClient is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestRuntimeSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(APP)
        self.req_headers = {"X-Actor-Id": "qa_user", "X-Actor-Role": "requester"}
        self.reviewer_headers = {"X-Actor-Id": "qa_reviewer", "X-Actor-Role": "reviewer"}
        self.approver_headers = {"X-Actor-Id": "qa_approver", "X-Actor-Role": "approver"}

    def _wait_status(self, task_id: str, expected: set[str], timeout: float = 5.0) -> dict | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            status_resp = self.client.get(f"/api/v1/task/status/{task_id}", headers=self.req_headers)
            self.assertEqual(status_resp.status_code, 200)
            payload = status_resp.json()
            if payload["status"] in expected:
                return payload
            time.sleep(0.1)
        return None

    def test_create_run_done_flow(self) -> None:
        create_resp = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "회의요약 생성",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "주간 운영회의",
                    "meeting_date": "2026-02-24",
                    "participants": ["Kim", "Lee"],
                    "notes": "업무A 진행\n업무B 리스크\n업무C 일정",
                },
                "requested_by": "qa_user",
            },
            headers=self.req_headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_1", "run_mode": "standard"},
            headers=self.req_headers,
        )
        self.assertEqual(run_resp.status_code, 202)

        final_payload = self._wait_status(task_id, {"DONE", "NEEDS_HUMAN_APPROVAL"})

        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["status"], "DONE")
        self.assertIn("result", final_payload)

    def test_policy_block_to_approval_flow(self) -> None:
        create_resp = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "외부전송 테스트",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "전송검토",
                    "meeting_date": "2026-02-24",
                    "participants": ["Ops"],
                    "notes": "요약 결과를 외부 전송 해주세요",
                },
                "requested_by": "qa_user",
            },
            headers=self.req_headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_2", "run_mode": "standard"},
            headers=self.req_headers,
        )
        self.assertEqual(run_resp.status_code, 202)

        approval_payload = self._wait_status(task_id, {"NEEDS_HUMAN_APPROVAL"})

        self.assertIsNotNone(approval_payload)
        self.assertEqual(approval_payload["status"], "NEEDS_HUMAN_APPROVAL")
        self.assertIn("approval_queue_id", approval_payload)

    def test_retry_exhausted_to_approval_flow(self) -> None:
        create_resp = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "실패 재시도 테스트",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "실패검증",
                    "meeting_date": "2026-02-24",
                    "participants": "Ops",  # invalid type by design
                    "notes": "내부 처리",
                },
                "requested_by": "qa_user",
            },
            headers=self.req_headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_3", "run_mode": "standard"},
            headers=self.req_headers,
        )
        self.assertEqual(run_resp.status_code, 202)

        approval_payload = self._wait_status(task_id, {"NEEDS_HUMAN_APPROVAL"})
        self.assertIsNotNone(approval_payload)
        self.assertEqual(approval_payload["approval_reason"], "retry_exhausted")

    def test_rbac_for_approval_endpoint(self) -> None:
        create_resp = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "권한 검증",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "권한검증",
                    "meeting_date": "2026-02-24",
                    "participants": ["Ops"],
                    "notes": "외부 전송 요청",
                },
                "requested_by": "qa_user",
            },
            headers=self.req_headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_4", "run_mode": "standard"},
            headers=self.req_headers,
        )
        self.assertEqual(run_resp.status_code, 202)

        approval_payload = self._wait_status(task_id, {"NEEDS_HUMAN_APPROVAL"})
        self.assertIsNotNone(approval_payload)
        queue_id = approval_payload["approval_queue_id"]

        forbidden = self.client.post(
            f"/api/v1/approvals/{queue_id}/approve",
            json={"acted_by": "qa_user", "comment": "requester approve attempt"},
            headers=self.req_headers,
        )
        self.assertEqual(forbidden.status_code, 403)

        ok = self.client.post(
            f"/api/v1/approvals/{queue_id}/approve",
            json={"acted_by": "qa_approver", "comment": "approved by approver"},
            headers=self.approver_headers,
        )
        self.assertEqual(ok.status_code, 200)

    def test_events_and_audit_summary(self) -> None:
        create_resp = self.client.post(
            "/api/v1/task/create",
            json={
                "title": "로그 검증",
                "template_type": "meeting_summary",
                "input": {
                    "meeting_title": "로그회의",
                    "meeting_date": "2026-02-24",
                    "participants": ["Kim", "Lee"],
                    "notes": "내부 논의",
                },
                "requested_by": "qa_user",
            },
            headers=self.req_headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_5", "run_mode": "standard"},
            headers=self.req_headers,
        )
        self.assertEqual(run_resp.status_code, 202)
        self.assertIsNotNone(self._wait_status(task_id, {"DONE", "NEEDS_HUMAN_APPROVAL"}))

        events_resp = self.client.get(f"/api/v1/task/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_resp.status_code, 200)
        events_payload = events_resp.json()
        self.assertGreaterEqual(events_payload["count"], 2)

        audit_resp = self.client.get("/api/v1/audit/summary", headers=self.reviewer_headers)
        self.assertEqual(audit_resp.status_code, 200)
        audit_payload = audit_resp.json()
        self.assertIn("blocked_policy_events", audit_payload)
        self.assertIn("policy_bypass_events", audit_payload)
        self.assertEqual(audit_payload["policy_bypass_events"], 0)


if __name__ == "__main__":
    unittest.main()
