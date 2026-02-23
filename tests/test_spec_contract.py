import unittest
from pathlib import Path


class TestSpecContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Path("app/main.py").read_text(encoding="utf-8")

    def test_required_statuses_exist(self) -> None:
        for status in (
            "READY",
            "RUNNING",
            "FAILED_RETRYABLE",
            "NEEDS_HUMAN_APPROVAL",
            "DONE",
        ):
            self.assertIn(status, self.source)

    def test_required_task_endpoints_exist(self) -> None:
        self.assertIn("def create_task", self.source)
        self.assertIn("def run_task", self.source)
        self.assertIn("def task_status", self.source)

    def test_required_approval_endpoints_exist(self) -> None:
        self.assertIn("def list_approvals", self.source)
        self.assertIn("def approve_queue_item", self.source)
        self.assertIn("def reject_queue_item", self.source)

    def test_policy_block_logging_exists(self) -> None:
        self.assertIn("BLOCKED_POLICY", self.source)

    def test_retry_policy_exists(self) -> None:
        self.assertIn("MAX_RETRY = 1", self.source)


if __name__ == "__main__":
    unittest.main()
