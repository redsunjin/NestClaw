from __future__ import annotations

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
class TestToolDraftRuntime(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.requester_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}
        self.approver_headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_approver', 'approver')}"}

    def test_api_creates_and_fetches_tool_draft(self) -> None:
        create_response = self.client.post(
            "/api/v1/tool-drafts",
            json={
                "requested_by": "qa_user",
                "request_text": "Slack 알림 도구를 추가하고 싶다",
                "tool_id": "slack.message.ops_broadcast",
                "title": "Ops Slack Broadcast",
            },
            headers=self.requester_headers,
        )
        self.assertEqual(create_response.status_code, 201)
        create_payload = create_response.json()
        self.assertEqual(create_payload["status"], "DRAFT_REVIEW_REQUIRED")
        self.assertEqual(create_payload["tool"]["external_system"], "slack")
        self.assertEqual(create_payload["tool"]["adapter"], "slack_api")
        self.assertEqual(create_payload["tool"]["method"], "message.send")

        get_response = self.client.get(
            f"/api/v1/tool-drafts/{create_payload['draft_id']}",
            headers=self.requester_headers,
        )
        self.assertEqual(get_response.status_code, 200)
        get_payload = get_response.json()
        self.assertIn("slack_api", get_payload["content"])
        self.assertEqual(get_payload["status"], "DRAFT_REVIEW_REQUIRED")

        apply_response = self.client.post(
            f"/api/v1/tool-drafts/{create_payload['draft_id']}/apply",
            json={"acted_by": "qa_approver"},
            headers=self.approver_headers,
        )
        self.assertEqual(apply_response.status_code, 200)
        apply_payload = apply_response.json()
        self.assertEqual(apply_payload["status"], "APPLIED")
        self.assertEqual(apply_payload["tool"]["tool_id"], "slack.message.ops_broadcast")

        list_response = self.client.get("/api/v1/tools", headers=self.requester_headers)
        self.assertEqual(list_response.status_code, 200)
        tool_ids = {item["tool_id"] for item in list_response.json()["items"]}
        self.assertIn("slack.message.ops_broadcast", tool_ids)


if __name__ == "__main__":
    unittest.main()
