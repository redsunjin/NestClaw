import json
import subprocess
import unittest
from pathlib import Path


PROFILE_PATH = Path("configs/deployment_bootstrap_profiles.json")
VALIDATOR = Path("scripts/validate_deployment_bootstrap_profiles.sh")


class TestStage11DeploymentBootstrapSmoke(unittest.TestCase):
    def test_profile_file_contains_three_canonical_profiles(self) -> None:
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        profiles = {item["profile_id"]: item for item in payload["profiles"]}
        self.assertEqual(set(profiles), {"local_dev", "operator_sidecar", "upper_agent_host"})
        self.assertTrue(profiles["local_dev"]["http"]["required"])
        self.assertTrue(profiles["operator_sidecar"]["mcp"]["required"])
        self.assertFalse(profiles["upper_agent_host"]["http"]["required"])
        self.assertEqual(profiles["upper_agent_host"]["mcp"]["transport"], "stdio")

    def test_validator_reports_ready(self) -> None:
        result = subprocess.run(
            ["bash", str(VALIDATOR), str(PROFILE_PATH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("# NestClaw Deployment Bootstrap Profile Validation", result.stdout)
        self.assertIn("- status: READY", result.stdout)


if __name__ == "__main__":
    unittest.main()
