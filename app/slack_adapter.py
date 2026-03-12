from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any
from urllib import error, request


DEFAULT_SLACK_API_BASE_URL = "https://slack.com/api"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def _is_truthy(raw: str | None, *, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _mask_payload(payload: dict[str, Any]) -> dict[str, Any]:
    masked = dict(payload)
    text = str(masked.get("text") or "").strip()
    if text:
        masked["text_preview"] = text[:120]
        masked["text"] = "[masked]"
    return masked


def execute_slack_action(
    *,
    method: str,
    payload: dict[str, Any],
    actor_context: dict[str, Any],
    dry_run: bool | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    normalized_method = str(method or "").strip()
    if normalized_method != "message.send":
        raise ValueError(f"unsupported slack method: {method}")

    channel = str(payload.get("channel") or "").strip()
    text = str(payload.get("text") or "").strip()
    if not channel:
        raise ValueError("slack payload missing channel")
    if not text:
        raise ValueError("slack payload missing text")

    effective_timeout = float(timeout_seconds or 3.0)
    if bool(dry_run):
        return {
            "provider": "slack_api",
            "mode": "dry-run",
            "executed": False,
            "method": normalized_method,
            "timeout_seconds": effective_timeout,
            "actor_id": actor_context.get("actor_id"),
            "actor_role": actor_context.get("actor_role"),
            "request_payload": _mask_payload(payload),
            "response": {"status": "accepted", "channel": channel},
            "generated_at": _now_iso(),
        }

    if not _is_truthy(os.getenv("NEWCLAW_ENABLE_SLACK_LIVE"), default=False):
        raise RuntimeError("slack_live_mode_not_enabled")

    token = str(os.getenv("NEWCLAW_SLACK_BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("missing_slack_bot_token")

    base_url = str(os.getenv("NEWCLAW_SLACK_API_BASE_URL") or DEFAULT_SLACK_API_BASE_URL).rstrip("/")
    req = request.Request(
        f"{base_url}/chat.postMessage",
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        data=json.dumps({"channel": channel, "text": text}, ensure_ascii=False).encode("utf-8"),
    )
    try:
        with request.urlopen(req, timeout=effective_timeout) as response:
            body = response.read().decode("utf-8")
    except error.URLError as exc:
        raise RuntimeError(f"slack_request_failed: {exc}") from exc

    parsed = json.loads(body)
    if not bool(parsed.get("ok")):
        raise RuntimeError(f"slack_api_error: {parsed.get('error') or 'unknown'}")

    return {
        "provider": "slack_api",
        "mode": "live",
        "executed": True,
        "method": normalized_method,
        "timeout_seconds": effective_timeout,
        "actor_id": actor_context.get("actor_id"),
        "actor_role": actor_context.get("actor_role"),
        "request_payload": _mask_payload(payload),
        "response": {
            "status": "ok",
            "channel": parsed.get("channel"),
            "external_ref": parsed.get("ts"),
        },
        "generated_at": _now_iso(),
    }
