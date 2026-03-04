from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Mapping


DEFAULT_TIMEOUT_SECONDS = 3.0
SUPPORTED_REDMINE_METHODS = {
    "issue.create",
    "issue.update",
    "issue.add_comment",
    "issue.assign",
    "issue.transition",
}
SENSITIVE_KEYS = {
    "authorization",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
}


class IncidentAdapterError(RuntimeError):
    """Raised when incident adapter inputs or runtime configuration are invalid."""


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def _is_truthy(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_dry_run(dry_run: bool | None) -> bool:
    if dry_run is not None:
        return dry_run
    return _is_truthy(os.getenv("NEWCLAW_INCIDENT_DRY_RUN"), default=True)


def _resolve_timeout(timeout_seconds: float | None) -> float:
    if timeout_seconds is None:
        return DEFAULT_TIMEOUT_SECONDS
    if timeout_seconds <= 0:
        raise IncidentAdapterError("timeout_seconds must be > 0")
    return float(timeout_seconds)


def _normalize_method(method: str) -> str:
    normalized = str(method).strip()
    if not normalized:
        raise IncidentAdapterError("method is required")
    return normalized


def _mask_scalar(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS:
        return "***REDACTED***"
    return value


def _mask_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, Mapping):
            masked[str(key)] = _mask_mapping(value)
        elif isinstance(value, list):
            masked[str(key)] = [_mask_value(str(key), item) for item in value]
        else:
            masked[str(key)] = _mask_scalar(str(key), value)
    return masked


def _mask_value(parent_key: str, value: Any) -> Any:
    if isinstance(value, Mapping):
        return _mask_mapping(value)
    if isinstance(value, list):
        return [_mask_value(parent_key, item) for item in value]
    return _mask_scalar(parent_key, value)


def mask_sensitive_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _mask_mapping(payload)


def execute_redmine_action(
    method: str,
    payload: Mapping[str, Any],
    actor_context: Mapping[str, Any],
    *,
    dry_run: bool | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """
    Stage 8 Redmine MCP adapter contract.

    Live calls are intentionally blocked at this phase; dry-run payloads are returned for pipeline integration.
    """
    method_name = _normalize_method(method)
    if method_name not in SUPPORTED_REDMINE_METHODS:
        raise IncidentAdapterError(f"unsupported redmine method: {method_name}")
    if not isinstance(payload, Mapping):
        raise IncidentAdapterError("payload must be a mapping")
    if not isinstance(actor_context, Mapping):
        raise IncidentAdapterError("actor_context must be a mapping")

    actor_id = str(actor_context.get("actor_id") or "").strip()
    actor_role = str(actor_context.get("actor_role") or "").strip().lower()
    if not actor_id or not actor_role:
        raise IncidentAdapterError("actor_context requires actor_id and actor_role")

    resolved_timeout = _resolve_timeout(timeout_seconds)
    masked_payload = mask_sensitive_payload(payload)

    if not _resolve_dry_run(dry_run):
        raise IncidentAdapterError("redmine mcp adapter is not configured for live mode")

    return {
        "provider": "redmine_mcp",
        "mode": "dry-run",
        "executed": False,
        "method": method_name,
        "timeout_seconds": resolved_timeout,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "request_payload": masked_payload,
        "response": {
            "status": "dry-run",
            "message": f"redmine action simulated for {method_name}",
            "external_ref": f"dryrun-{method_name.replace('.', '-')}",
        },
        "generated_at": _now_iso(),
    }
