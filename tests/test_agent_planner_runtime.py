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
class TestAgentPlannerRuntime(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}
        self.reviewer_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_reviewer', 'reviewer')}"}
        self.payload = {
            "task_kind": "task",
            "request_text": "운영회의를 요약하고 후속 티켓을 만들고 슬랙으로 공유해줘",
            "requested_by": "qa_user",
            "metadata": {
                "meeting_title": "ops sync",
                "meeting_date": "2026-03-13",
                "participants": ["Kim"],
                "notes": "summary for operations team",
                "notify_channel": "#ops-alerts",
                "ticket_project_id": "OPS",
                "create_ticket": True,
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

    def test_task_runtime_records_fallback_planning_provenance(self) -> None:
        with patch.dict("os.environ", {"NEWCLAW_ENABLE_LLM_PLANNER": "0"}, clear=False):
            response = self.client.post("/api/v1/agent/submit", json=self.payload, headers=self.requester_headers)
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        payload = self._wait_agent_status(task_id, {"DONE"})
        self.assertIsNotNone(payload)
        self.assertEqual(payload["planning_provenance"]["source"], "heuristic_fallback")
        self.assertTrue(payload["planning_provenance"]["degraded_mode"])
        self.assertEqual(
            [item["tool_id"] for item in payload["planned_actions"]],
            ["internal.summary.generate", "redmine.issue.create", "slack.message.send"],
        )
        self.assertIn(
            "redmine.issue.create",
            [item["tool_id"] for item in payload["planning_provenance"]["eligible_tools"] if item["eligible"]],
        )
        self.assertEqual(payload["action_results"][1]["tool_id"], "redmine.issue.create")
        self.assertEqual(payload["action_results"][1]["mode"], "dry-run")
        self.assertIn("# 회의 결과 요약", payload["action_results"][1]["request_payload"]["description"])
        self.assertEqual(payload["action_results"][2]["tool_id"], "slack.message.send")
        self.assertIn("# 회의 결과 요약", payload["action_results"][2]["request_payload"]["text_preview"])

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        planning_events = [item for item in events_response.json()["items"] if item["event_type"] == "TASK_PLAN_GENERATED"]
        self.assertEqual(len(planning_events), 1)
        self.assertEqual(planning_events[0]["source"], "heuristic_fallback")

    def test_task_runtime_uses_llm_planner_when_enabled(self) -> None:
        planner_json = (
            '{"actions":['
            '{"tool_id":"internal.summary.generate","reason":"generate summary first"},'
            '{"tool_id":"redmine.issue.create","reason":"open follow-up ticket"},'
            '{"tool_id":"slack.message.send","reason":"notify team","payload_overrides":{"channel":"#ops-alerts"}}'
            '],"confidence":0.93,"rationale":"summary then ticket then notify"}'
        )
        with (
            patch.dict(
                "os.environ",
                {"NEWCLAW_ENABLE_LLM_PLANNER": "1", "NEWCLAW_ENABLE_LLM_SUMMARY": "0"},
                clear=False,
            ),
            patch("app.agent_planner._detect_openai_compatible_model", return_value="lmstudio-loaded-model"),
            patch("app.agent_planner._call_planner_openai_compatible_chat", return_value=planner_json),
        ):
            response = self.client.post("/api/v1/agent/submit", json=self.payload, headers=self.requester_headers)
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]

        payload = self._wait_agent_status(task_id, {"DONE"})
        self.assertIsNotNone(payload)
        self.assertEqual(payload["planning_provenance"]["source"], "llm")
        self.assertFalse(payload["planning_provenance"]["degraded_mode"])
        self.assertEqual(payload["planning_provenance"]["provider_selection"]["provider_id"], "local_lmstudio")
        self.assertEqual(
            [item["tool_id"] for item in payload["planned_actions"]],
            ["internal.summary.generate", "redmine.issue.create", "slack.message.send"],
        )
        self.assertIn(
            "redmine.issue.create",
            [item["tool_id"] for item in payload["planning_provenance"]["eligible_tools"] if item["eligible"]],
        )
        self.assertIn("# 회의 결과 요약", payload["action_results"][1]["request_payload"]["description"])
        self.assertIn("# 회의 결과 요약", payload["action_results"][2]["request_payload"]["text_preview"])

        events_response = self.client.get(f"/api/v1/agent/events/{task_id}", headers=self.reviewer_headers)
        self.assertEqual(events_response.status_code, 200)
        fallback_events = [item for item in events_response.json()["items"] if item["event_type"] == "TASK_PLAN_FALLBACK"]
        self.assertEqual(fallback_events, [])


if __name__ == "__main__":
    unittest.main()
