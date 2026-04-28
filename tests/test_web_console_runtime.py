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
        self.assertIn("quick-role-note", body)
        self.assertIn('data-role-scope="approver admin"', body)
        self.assertIn("Planner Provenance", body)
        self.assertIn("quick-planner-signals", body)
        self.assertIn("quick-action-rail", body)
        self.assertIn("quick-execution-rail", body)
        self.assertIn("/static/agent-quickstart.js", body)

        console_response = self.client.get("/console")
        self.assertEqual(console_response.status_code, 200)
        console_body = console_response.text
        self.assertIn("NestClaw Web Console", console_body)
        self.assertIn("Capability 카탈로그", console_body)
        self.assertIn("승인 상세 / 이력", console_body)
        self.assertIn("Capability / Readiness", console_body)
        self.assertIn("capability-summary", console_body)
        self.assertIn("role-mode-summary", console_body)
        self.assertIn("run-mode-note", console_body)
        self.assertIn("planner-signal-strip", console_body)
        self.assertIn("planner-rationale", console_body)
        self.assertIn("execution-detail", console_body)
        self.assertIn("Stage 12 Job Runs", console_body)
        self.assertIn("job-run-list", console_body)
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
        self.assertIn("renderPlannerSignals", quick_js.text)
        self.assertIn("renderRail", quick_js.text)
        self.assertIn("stateSummaryContext", quick_js.text)
        self.assertIn("canonical_reason", quick_js.text)
        self.assertIn("applyRoleVisibility", quick_js.text)
        self.assertIn("quick-planner", self.client.get("/").text)
        self.assertIn("quick-submit", self.client.get("/").text)

        js_response = self.client.get("/static/agent-console.js")
        self.assertEqual(js_response.status_code, 200)
        self.assertIn("loadTools", js_response.text)
        self.assertIn("submitAgent", js_response.text)
        self.assertIn("plannerSummaryLines", js_response.text)
        self.assertIn("renderSignalStrip", js_response.text)
        self.assertIn("renderActionInspector", js_response.text)
        self.assertIn("rationaleLines", js_response.text)
        self.assertIn("stateSummaryContext", js_response.text)
        self.assertIn("canonical_reason", js_response.text)
        self.assertIn("roleProfile", js_response.text)
        self.assertIn("applyRunModeVisibility", js_response.text)
        self.assertIn("/api/v1/agent/submit", js_response.text)
        self.assertIn("/api/v1/agent/recent", js_response.text)
        self.assertIn("/api/v1/jobs/runs", js_response.text)
        self.assertIn("loadJobHistory", js_response.text)
        self.assertIn("renderJobRuns", js_response.text)
        self.assertIn("data-load-job-task", js_response.text)
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
        self.assertIn(".job-run-card", css_response.text)
        self.assertIn(".job-history-block", css_response.text)
        self.assertIn(".report-preview-card", css_response.text)
        self.assertIn(".approval-history-card", css_response.text)
        self.assertIn(".console-layout", css_response.text)
        self.assertIn(".signal-strip", css_response.text)
        self.assertIn(".action-rail", css_response.text)

        quick_css = self.client.get("/static/agent-quickstart.css")
        self.assertEqual(quick_css.status_code, 200)
        self.assertIn(".results-grid", quick_css.text)
        self.assertIn(".recent-row", quick_css.text)
        self.assertIn(".flow-grid", quick_css.text)
        self.assertIn(".signal-chip", quick_css.text)


if __name__ == "__main__":
    unittest.main()
