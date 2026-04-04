from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout


try:
    from fastapi.testclient import TestClient
    from app.auth import issue_dev_jwt
    from app import cli as cli_module
    from app.main import APP
    from app import main as main_module
    from tests.runtime_test_utils import reset_runtime_state
except Exception as exc:  # pragma: no cover - environment dependent
    TestClient = None
    cli_module = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(TestClient is None or cli_module is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestCapabilityManifestRuntime(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(APP)
        self.headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}

    def test_http_capability_manifest_exposes_current_runtime_scope(self) -> None:
        response = self.client.get("/api/v1/capabilities", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["product_posture"], "orchestration_backend_with_human_dashboard")
        self.assertEqual(payload["primary_entrypoint"], "agent.submit/status/events")
        families = {item["kind"] for item in payload["workflow_families"]}
        self.assertEqual(families, {"task", "incident"})
        self.assertIn("requester", payload["roles"])
        self.assertIn("approver", payload["roles"])
        self.assertGreaterEqual(int(payload["tool_catalog"]["count"]), 6)
        tool_ids = {item["tool_id"] for item in payload["tool_catalog"]["items"]}
        self.assertIn("internal.summary.generate", tool_ids)
        self.assertIn("redmine.issue.create", tool_ids)
        self.assertIn("slack.message.send", tool_ids)
        self.assertIn("catalog.manifest", payload["controls"]["safe_for_upper_agents"])

    def test_cli_capabilities_command_returns_manifest_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = cli_module.main(["capabilities", "--actor-id", "qa_user", "--json"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue().strip() or "{}")
        self.assertEqual(payload["primary_entrypoint"], "agent.submit/status/events")
        self.assertIn("mcp", {item["surface"] for item in payload["delivery_surfaces"]})


if __name__ == "__main__":
    unittest.main()
