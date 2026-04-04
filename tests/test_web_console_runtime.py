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

    def test_root_serves_quickstart_and_console_serves_advanced_ui(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        body = response.text
        self.assertIn("NestClaw Quickstart", body)
        self.assertIn("한 줄 요청을 안전하게 실행", body)
        self.assertIn("Identity", body)
        self.assertIn("Runtime", body)
        self.assertIn("Planner Provenance", body)
        self.assertIn("/static/agent-quickstart.js", body)

        console_response = self.client.get("/console")
        self.assertEqual(console_response.status_code, 200)
        console_body = console_response.text
        self.assertIn("NestClaw Web Console", console_body)
        self.assertIn("Capability 카탈로그", console_body)
        self.assertIn("승인 상세 / 이력", console_body)
        self.assertIn("Capability / Readiness", console_body)
        self.assertIn("capability-summary", console_body)
        self.assertIn("아직 planner 정보가 없습니다.", console_body)
        self.assertIn("/static/agent-console.js", console_body)

    def test_static_assets_are_served(self) -> None:
        quick_js = self.client.get("/static/agent-quickstart.js")
        self.assertEqual(quick_js.status_code, 200)
        self.assertIn("/api/v1/agent/submit", quick_js.text)
        self.assertIn("/api/v1/agent/status/", quick_js.text)
        self.assertIn("/api/v1/agent/report/", quick_js.text)
        self.assertIn("/api/v1/approvals/", quick_js.text)
        self.assertIn("/api/v1/agent/recent", quick_js.text)
        self.assertIn("plannerSummaryFromPayload", quick_js.text)
        self.assertIn("quick-planner", self.client.get("/").text)
        self.assertIn("quick-submit", self.client.get("/").text)

        js_response = self.client.get("/static/agent-console.js")
        self.assertEqual(js_response.status_code, 200)
        self.assertIn("loadTools", js_response.text)
        self.assertIn("submitAgent", js_response.text)
        self.assertIn("plannerSummaryLines", js_response.text)
        self.assertIn("planDetailLines", js_response.text)
        self.assertIn("/api/v1/agent/submit", js_response.text)
        self.assertIn("/api/v1/agent/recent", js_response.text)
        self.assertIn("/api/v1/agent/report/", js_response.text)
        self.assertIn("/api/v1/agent/status/", js_response.text)
        self.assertIn("/api/v1/agent/events/", js_response.text)
        self.assertIn("/api/v1/capabilities", js_response.text)
        self.assertIn("/api/v1/approvals", js_response.text)
        self.assertIn("/api/v1/approvals/", js_response.text)
        self.assertIn("${queueId}/${action}", js_response.text)
        self.assertIn("data-approve", js_response.text)
        self.assertIn("data-reject", js_response.text)
        self.assertIn("data-approval-detail", js_response.text)
        self.assertIn("data-load-task", js_response.text)
        self.assertIn("data-preview-report", js_response.text)
        self.assertIn("data-open-report", js_response.text)
        self.assertIn("/api/v1/tool-drafts", js_response.text)

        css_response = self.client.get("/static/agent-console.css")
        self.assertEqual(css_response.status_code, 200)
        self.assertIn(".tool-card", css_response.text)
        self.assertIn(".summary-card", css_response.text)
        self.assertIn(".approval-card", css_response.text)
        self.assertIn(".history-card", css_response.text)
        self.assertIn(".report-preview-card", css_response.text)
        self.assertIn(".approval-history-card", css_response.text)
        self.assertIn(".console-layout", css_response.text)

        quick_css = self.client.get("/static/agent-quickstart.css")
        self.assertEqual(quick_css.status_code, 200)
        self.assertIn(".results-grid", quick_css.text)
        self.assertIn(".recent-card", quick_css.text)


if __name__ == "__main__":
    unittest.main()
