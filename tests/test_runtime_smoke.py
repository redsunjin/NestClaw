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
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_1", "run_mode": "standard"},
        )
        self.assertEqual(run_resp.status_code, 202)

        deadline = time.time() + 5
        final_payload = None
        while time.time() < deadline:
            status_resp = self.client.get(f"/api/v1/task/status/{task_id}")
            self.assertEqual(status_resp.status_code, 200)
            payload = status_resp.json()
            if payload["status"] in {"DONE", "NEEDS_HUMAN_APPROVAL"}:
                final_payload = payload
                break
            time.sleep(0.1)

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
        )
        self.assertEqual(create_resp.status_code, 201)
        task_id = create_resp.json()["task_id"]

        run_resp = self.client.post(
            "/api/v1/task/run",
            json={"task_id": task_id, "idempotency_key": "smoke_2", "run_mode": "standard"},
        )
        self.assertEqual(run_resp.status_code, 202)

        deadline = time.time() + 5
        approval_payload = None
        while time.time() < deadline:
            status_resp = self.client.get(f"/api/v1/task/status/{task_id}")
            self.assertEqual(status_resp.status_code, 200)
            payload = status_resp.json()
            if payload["status"] == "NEEDS_HUMAN_APPROVAL":
                approval_payload = payload
                break
            time.sleep(0.1)

        self.assertIsNotNone(approval_payload)
        self.assertEqual(approval_payload["status"], "NEEDS_HUMAN_APPROVAL")
        self.assertIn("approval_queue_id", approval_payload)


if __name__ == "__main__":
    unittest.main()
