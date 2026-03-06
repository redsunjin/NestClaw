import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.incident_mcp import IncidentAdapterError as McpAdapterError
from app.incident_mcp import execute_redmine_action, mask_sensitive_payload
from app.incident_rag import IncidentAdapterError as RagAdapterError
from app.incident_rag import fetch_knowledge_evidence, fetch_system_signals


class _FakeResponse:
    def __init__(self, payload: object, status_code: int = 200, text: str = "") -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text or str(payload)

    def json(self) -> object:
        return self._payload


class _RecordingClient:
    calls: list[dict[str, object]] = []

    def __init__(self, *, timeout: float, verify: bool) -> None:
        self.timeout = timeout
        self.verify = verify

    def __enter__(self) -> "_RecordingClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def post(self, url: str, *, json: dict[str, object], headers: dict[str, str]) -> _FakeResponse:
        self.calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": self.timeout,
                "verify": self.verify,
            }
        )
        return _FakeResponse({"status": "created", "issue_id": "RM-123"})


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

    def test_execute_redmine_action_live_mode_requires_endpoint(self) -> None:
        with patch.dict(os.environ, {"NEWCLAW_STAGE8_LIVE_ENABLED": "1"}, clear=False):
            with self.assertRaises(McpAdapterError):
                execute_redmine_action(
                    "issue.create",
                    {"subject": "incident"},
                    {"actor_id": "ops_user", "actor_role": "approver"},
                    dry_run=False,
                )

    def test_execute_redmine_action_live_mode_posts_to_http_bridge(self) -> None:
        _RecordingClient.calls.clear()
        fake_httpx = SimpleNamespace(Client=_RecordingClient)
        with patch("app.incident_mcp.httpx", fake_httpx):
            with patch.dict(
                os.environ,
                {
                    "NEWCLAW_STAGE8_LIVE_ENABLED": "1",
                    "NEWCLAW_REDMINE_MCP_ENDPOINT": "https://sandbox.example/api/redmine",
                    "NEWCLAW_REDMINE_MCP_TOKEN": "bridge-token",
                    "NEWCLAW_REDMINE_MCP_VERIFY_TLS": "false",
                },
                clear=False,
            ):
                payload = execute_redmine_action(
                    "issue.create",
                    {"subject": "incident", "token": "secret-token"},
                    {"actor_id": "ops_user", "actor_role": "approver"},
                    dry_run=False,
                    timeout_seconds=4.5,
                )

        self.assertEqual(payload["mode"], "live")
        self.assertTrue(payload["executed"])
        self.assertEqual(payload["response"]["issue_id"], "RM-123")
        self.assertEqual(payload["response"]["external_ref"], "RM-123")
        self.assertEqual(payload["request_payload"]["token"], "***REDACTED***")

        self.assertEqual(len(_RecordingClient.calls), 1)
        call = _RecordingClient.calls[0]
        self.assertEqual(call["url"], "https://sandbox.example/api/redmine")
        self.assertEqual(call["timeout"], 4.5)
        self.assertFalse(call["verify"])
        self.assertEqual(call["headers"]["Authorization"], "Bearer bridge-token")
        self.assertEqual(call["json"]["method"], "issue.create")
        self.assertEqual(call["json"]["payload"]["token"], "secret-token")

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
