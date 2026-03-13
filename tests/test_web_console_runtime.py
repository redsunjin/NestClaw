from __future__ import annotations

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
class TestWebConsoleRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(APP)

    def test_root_serves_minimal_console(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        body = response.text
        self.assertIn("NestClaw Web Console", body)
        self.assertIn("도구 카탈로그", body)
        self.assertIn("Agent 실행", body)
        self.assertIn("실행 상태", body)
        self.assertIn("승인 큐", body)
        self.assertIn("/static/agent-console.js", body)

    def test_static_assets_are_served(self) -> None:
        js_response = self.client.get("/static/agent-console.js")
        self.assertEqual(js_response.status_code, 200)
        self.assertIn("loadTools", js_response.text)
        self.assertIn("submitAgent", js_response.text)
        self.assertIn("/api/v1/agent/submit", js_response.text)
        self.assertIn("/api/v1/agent/status/", js_response.text)
        self.assertIn("/api/v1/agent/events/", js_response.text)
        self.assertIn("/api/v1/approvals", js_response.text)
        self.assertIn("${queueId}/${action}", js_response.text)
        self.assertIn("data-approve", js_response.text)
        self.assertIn("data-reject", js_response.text)
        self.assertIn("/api/v1/tool-drafts", js_response.text)

        css_response = self.client.get("/static/agent-console.css")
        self.assertEqual(css_response.status_code, 200)
        self.assertIn(".tool-card", css_response.text)
        self.assertIn(".summary-card", css_response.text)
        self.assertIn(".approval-card", css_response.text)


if __name__ == "__main__":
    unittest.main()
