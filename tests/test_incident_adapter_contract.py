import unittest

from app.incident_mcp import IncidentAdapterError as McpAdapterError
from app.incident_mcp import execute_redmine_action, mask_sensitive_payload
from app.incident_rag import IncidentAdapterError as RagAdapterError
from app.incident_rag import fetch_knowledge_evidence, fetch_system_signals


class TestIncidentAdapterContract(unittest.TestCase):
    def test_fetch_knowledge_evidence_dry_run_contract(self) -> None:
        payload = fetch_knowledge_evidence("api latency", "platform", "90d", dry_run=True, timeout_seconds=2.5)
        self.assertEqual(payload["provider"], "knowledge_rag")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["team"], "platform")
        self.assertEqual(payload["timeout_seconds"], 2.5)
        self.assertEqual(len(payload["evidence"]), 1)

    def test_fetch_system_signals_dry_run_contract(self) -> None:
        payload = fetch_system_signals("inc_001", "billing-api", "15m", dry_run=True)
        self.assertEqual(payload["provider"], "system_rag")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["incident_id"], "inc_001")
        self.assertEqual(len(payload["signals"]), 1)

    def test_fetch_knowledge_evidence_live_mode_not_configured(self) -> None:
        with self.assertRaises(RagAdapterError):
            fetch_knowledge_evidence("q", "team", "7d", dry_run=False)

    def test_execute_redmine_action_dry_run_masks_sensitive_fields(self) -> None:
        payload = execute_redmine_action(
            "issue.create",
            {"subject": "incident", "token": "secret-token"},
            {"actor_id": "ops_user", "actor_role": "approver"},
            dry_run=True,
        )
        self.assertEqual(payload["provider"], "redmine_mcp")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["request_payload"]["token"], "***REDACTED***")

    def test_execute_redmine_action_live_mode_not_configured(self) -> None:
        with self.assertRaises(McpAdapterError):
            execute_redmine_action(
                "issue.create",
                {"subject": "incident"},
                {"actor_id": "ops_user", "actor_role": "approver"},
                dry_run=False,
            )

    def test_execute_redmine_action_rejects_unsupported_method(self) -> None:
        with self.assertRaises(McpAdapterError):
            execute_redmine_action(
                "issue.delete",
                {"subject": "incident"},
                {"actor_id": "ops_user", "actor_role": "approver"},
                dry_run=True,
            )

    def test_mask_sensitive_payload_nested(self) -> None:
        masked = mask_sensitive_payload(
            {
                "auth": {"token": "abc", "password": "pw"},
                "array": [{"api_key": "k1"}, {"description": "ok"}],
            }
        )
        self.assertEqual(masked["auth"]["token"], "***REDACTED***")
        self.assertEqual(masked["auth"]["password"], "***REDACTED***")
        self.assertEqual(masked["array"][0]["api_key"], "***REDACTED***")
        self.assertEqual(masked["array"][1]["description"], "ok")


if __name__ == "__main__":
    unittest.main()
