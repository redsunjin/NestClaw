import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path("scripts/validate_stage8_env_handoff.sh")


class TestStage11EnvHandoffSmoke(unittest.TestCase):
    def test_validator_reports_blocked_when_required_env_missing(self) -> None:
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if not k.startswith("NEWCLAW_STAGE8_") and not k.startswith("NEWCLAW_REDMINE_MCP")},
            check=False,
        )
        self.assertEqual(result.returncode, 20)
        self.assertIn("- status: BLOCKED", result.stdout)
        self.assertIn("NEWCLAW_STAGE8_SANDBOX_ENABLED", result.stdout)
        self.assertIn("NEWCLAW_REDMINE_MCP_ENDPOINT", result.stdout)

    def test_validator_reports_ready_for_filled_env_file(self) -> None:
        payload = textwrap.dedent(
            """
            NEWCLAW_STAGE8_SANDBOX_ENABLED=1
            NEWCLAW_STAGE8_SANDBOX_BASE_URL=https://redmine-sandbox.example.internal
            NEWCLAW_STAGE8_SANDBOX_PROJECT=OPS-SANDBOX
            NEWCLAW_STAGE8_LIVE_ENABLED=true
            NEWCLAW_REDMINE_MCP_ENDPOINT=https://redmine-mcp.example.internal/api
            NEWCLAW_REDMINE_MCP_VERIFY_TLS=true
            NEWCLAW_STAGE8_SANDBOX_ASSIGNEE=ops_oncall
            NEWCLAW_STAGE8_SANDBOX_TRANSITION="In Progress"
            NEWCLAW_STAGE8_LIVE_REQUESTED_BY=stage8_live_runner
            """
        ).strip()
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
            env_file = handle.name
        self.addCleanup(lambda: Path(env_file).unlink(missing_ok=True))

        result = subprocess.run(
            ["bash", str(SCRIPT), env_file],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("- status: READY", result.stdout)
        self.assertIn("recommended_configured:", result.stdout)
        self.assertIn("run_stage8_readiness_bundle.sh", result.stdout)


if __name__ == "__main__":
    unittest.main()
