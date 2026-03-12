from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.slack_adapter import execute_slack_action


class _FakeResponse:
    def __init__(self, body: dict[str, object]) -> None:
        self._body = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class TestSlackAdapterContract(unittest.TestCase):
    def test_execute_slack_action_dry_run_masks_text(self) -> None:
        payload = execute_slack_action(
            method="message.send",
            payload={"channel": "#ops-alerts", "text": "customer outage"},
            actor_context={"actor_id": "qa_user", "actor_role": "requester"},
            dry_run=True,
            timeout_seconds=2.5,
        )

        self.assertEqual(payload["provider"], "slack_api")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["request_payload"]["text"], "[masked]")
        self.assertEqual(payload["response"]["channel"], "#ops-alerts")

    def test_execute_slack_action_live_requires_enable_flag(self) -> None:
        with self.assertRaises(RuntimeError):
            execute_slack_action(
                method="message.send",
                payload={"channel": "#ops-alerts", "text": "customer outage"},
                actor_context={"actor_id": "qa_user", "actor_role": "requester"},
                dry_run=False,
            )

    def test_execute_slack_action_live_requires_token(self) -> None:
        with patch.dict("os.environ", {"NEWCLAW_ENABLE_SLACK_LIVE": "1"}, clear=False):
            with self.assertRaises(RuntimeError):
                execute_slack_action(
                    method="message.send",
                    payload={"channel": "#ops-alerts", "text": "customer outage"},
                    actor_context={"actor_id": "qa_user", "actor_role": "requester"},
                    dry_run=False,
                )

    def test_execute_slack_action_live_posts_to_api(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "NEWCLAW_ENABLE_SLACK_LIVE": "1",
                "NEWCLAW_SLACK_BOT_TOKEN": "token",
                "NEWCLAW_SLACK_API_BASE_URL": "https://slack.test.local/api",
            },
            clear=False,
        ):
            with patch("app.slack_adapter.request.urlopen", return_value=_FakeResponse({"ok": True, "channel": "C1", "ts": "1.23"})):
                payload = execute_slack_action(
                    method="message.send",
                    payload={"channel": "#ops-alerts", "text": "customer outage"},
                    actor_context={"actor_id": "qa_user", "actor_role": "requester"},
                    dry_run=False,
                    timeout_seconds=4.0,
                )

        self.assertEqual(payload["mode"], "live")
        self.assertTrue(payload["executed"])
        self.assertEqual(payload["response"]["external_ref"], "1.23")


if __name__ == "__main__":
    unittest.main()
