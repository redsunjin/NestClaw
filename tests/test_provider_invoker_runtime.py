from __future__ import annotations

import time
import unittest
from unittest.mock import patch


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
class TestProviderInvokerRuntime(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}
        self.reviewer_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_reviewer', 'reviewer')}"}
        self.payload = {
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
        }

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

    def test_agent_task_records_fallback_invocation_metadata(self) -> None:
        response = self.client.post("/api/v1/agent/submit", json=self.payload, headers=self.requester_headers)
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        payload = self._wait_agent_status(task_id, {"DONE"})
        self.assertIsNotNone(payload)
        self.assertEqual(payload["status"], "DONE")
        self.assertEqual(payload["provider_invocation"]["result_source"], "template_fallback")
        self.assertEqual(payload["provider_invocation"]["fallback_reason"], "live_summary_disabled")

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        invocation_events = [item for item in events_response.json()["items"] if item["event_type"] == "MODEL_PROVIDER_INVOKED"]
        self.assertEqual(len(invocation_events), 1)
        self.assertEqual(invocation_events[0]["result_source"], "template_fallback")

    def test_agent_task_uses_live_provider_when_enabled(self) -> None:
        live_summary = (
            "# 회의 결과 요약\n\n"
            "## 핵심 논점\n- live summary\n\n"
            "## 액션 아이템\n| 항목 | 담당자 | 기한 | 우선순위 | 상태 |\n|---|---|---|---|---|\n"
            "| Action 1 | Kim | 2026-03-13 | High | Open |\n\n"
            "## 확인 필요\n- verify\n"
        )
        with patch.dict(
            "os.environ",
            {"NEWCLAW_ENABLE_LLM_SUMMARY": "1", "NEWCLAW_OPENAI_BASE_URL": "http://127.0.0.1:1234"},
            clear=False,
        ):
            with patch("app.provider_invoker._call_summary_openai_compatible_chat", return_value=live_summary):
                response = self.client.post("/api/v1/agent/submit", json=self.payload, headers=self.requester_headers)
                self.assertEqual(response.status_code, 202)
                task_id = response.json()["task_id"]
                payload = self._wait_agent_status(task_id, {"DONE"})
        self.assertIsNotNone(payload)
        self.assertEqual(payload["status"], "DONE")
        self.assertEqual(payload["provider_invocation"]["result_source"], "live_provider")
        self.assertTrue(payload["provider_invocation"]["invoked"])
        report_path = payload["result"]["report_path"]
        with open(report_path, "r", encoding="utf-8") as handle:
            report_text = handle.read()
        self.assertIn("live summary", report_text)


if __name__ == "__main__":
    unittest.main()
