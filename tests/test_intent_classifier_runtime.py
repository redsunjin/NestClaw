from __future__ import annotations

import os
import time
import unittest
from unittest.mock import patch


try:
    from fastapi.testclient import TestClient

    from app import main as main_module
    from app.auth import issue_dev_jwt
    from app.intent_classifier import IntentClassification
    from app.main import APP
    from tests.runtime_test_utils import reset_runtime_state
except Exception as exc:  # pragma: no cover - environment dependent
    TestClient = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(TestClient is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestIntentClassifierRuntime(unittest.TestCase):
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

    def test_auto_route_uses_classifier_result_for_task_override(self) -> None:
        classification = IntentClassification(
            resolved_kind="task",
            source="llm",
            confidence=0.93,
            rationale="user asked for a summary deliverable",
            provider_selection={"provider_id": "local_lmstudio", "engine": "lmstudio", "model": "auto"},
        )
        with patch.object(main_module.INTENT_CLASSIFIER, "classify", return_value=classification):
            response = self.client.post(
                "/api/v1/agent/submit",
                json={
                    "task_kind": "auto",
                    "request_text": "billing-api 장애 대응 내용을 요약 보고서로만 정리해줘",
                    "requested_by": "qa_user",
                },
                headers=self.requester_headers,
            )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["resolved_kind"], "task")
        self.assertEqual(payload["intent_classification"]["source"], "llm")
        task_id = str(payload["task_id"])

        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["resolved_kind"], "task")
        self.assertEqual(final_payload["intent_classification"]["source"], "llm")

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        classified = [item for item in events_response.json()["items"] if item["event_type"] == "INTENT_CLASSIFIED"]
        self.assertEqual(len(classified), 1)
        self.assertEqual(classified[0]["source"], "llm")
        self.assertEqual(classified[0]["provider_id"], "local_lmstudio")

    def test_auto_route_reports_heuristic_fallback_when_llm_is_disabled(self) -> None:
        with patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_INTENT": "0"}, clear=False):
            response = self.client.post(
                "/api/v1/agent/submit",
                json={
                    "task_kind": "auto",
                    "request_text": "billing-api 장애 대응용 티켓을 생성해줘",
                    "requested_by": "qa_user",
                    "metadata": {"service": "billing-api", "severity": "low", "time_window": "15m"},
                },
                headers=self.requester_headers,
            )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["resolved_kind"], "incident")
        self.assertEqual(payload["intent_classification"]["source"], "heuristic_fallback")
        task_id = str(payload["task_id"])

        final_payload = self._wait_status(task_id, {"DONE"})
        self.assertIsNotNone(final_payload)
        self.assertEqual(final_payload["resolved_kind"], "incident")
        self.assertEqual(final_payload["intent_classification"]["source"], "heuristic_fallback")


if __name__ == "__main__":
    unittest.main()
