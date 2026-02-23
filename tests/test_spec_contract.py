import unittest
from pathlib import Path


class TestSpecContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Path("app/main.py").read_text(encoding="utf-8")
        cls.auth_source = Path("app/auth.py").read_text(encoding="utf-8")

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
        self.assertIn("def task_events", self.source)

    def test_required_approval_endpoints_exist(self) -> None:
        self.assertIn("def list_approvals", self.source)
        self.assertIn("def approve_queue_item", self.source)
        self.assertIn("def reject_queue_item", self.source)
        self.assertIn("def audit_summary", self.source)

    def test_policy_block_logging_exists(self) -> None:
        self.assertIn("BLOCKED_POLICY", self.source)

    def test_retry_policy_exists(self) -> None:
        self.assertIn("MAX_RETRY = 1", self.source)

    def test_rbac_headers_exist(self) -> None:
        self.assertIn("X-Actor-Role", self.auth_source)
        self.assertIn("X-Actor-Id", self.auth_source)
        self.assertIn("Authorization", self.auth_source)
        self.assertIn("X-SSO-User", self.auth_source)
        self.assertIn("X-SSO-Role", self.auth_source)

    def test_sqlite_persistence_exists(self) -> None:
        persistence_source = Path("app/persistence.py").read_text(encoding="utf-8")
        self.assertIn("class SQLiteStateStore", persistence_source)
        self.assertIn("CREATE TABLE IF NOT EXISTS tasks", persistence_source)


if __name__ == "__main__":
    unittest.main()
