from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Mapping

try:
    import httpx
except ImportError:  # pragma: no cover - optional runtime dependency
    httpx = None


DEFAULT_TIMEOUT_SECONDS = 3.0
LIVE_ENABLE_ENV = "NEWCLAW_STAGE8_LIVE_ENABLED"
MCP_ENDPOINT_ENV = "NEWCLAW_REDMINE_MCP_ENDPOINT"
MCP_TOKEN_ENV = "NEWCLAW_REDMINE_MCP_TOKEN"
MCP_VERIFY_TLS_ENV = "NEWCLAW_REDMINE_MCP_VERIFY_TLS"
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


def _resolve_live_endpoint() -> str:
    endpoint = str(os.getenv(MCP_ENDPOINT_ENV) or "").strip()
    if not endpoint:
        raise IncidentAdapterError("redmine mcp endpoint is not configured for live mode")
    return endpoint


def _resolve_live_verify_tls() -> bool:
    return _is_truthy(os.getenv(MCP_VERIFY_TLS_ENV), default=True)


def _normalize_live_response(method_name: str, response_payload: Any) -> dict[str, Any]:
    if not isinstance(response_payload, Mapping):
        raise IncidentAdapterError("redmine mcp live response must be a mapping")
    normalized = dict(response_payload)
    normalized.setdefault("status", "ok")
    normalized.setdefault("message", f"redmine action executed for {method_name}")
    if "external_ref" not in normalized:
        normalized["external_ref"] = (
            normalized.get("issue_id")
            or normalized.get("ticket_id")
            or normalized.get("id")
        )
    return normalized


def _execute_live_redmine_action(
    method_name: str,
    payload: Mapping[str, Any],
    actor_id: str,
    actor_role: str,
    resolved_timeout: float,
    masked_payload: Mapping[str, Any],
) -> dict[str, Any]:
    if httpx is None:
        raise IncidentAdapterError("httpx dependency unavailable for live mode")
    if not _is_truthy(os.getenv(LIVE_ENABLE_ENV), default=False):
        raise IncidentAdapterError("stage8 live mode is not enabled")

    endpoint = _resolve_live_endpoint()
    headers = {"Content-Type": "application/json"}
    token = str(os.getenv(MCP_TOKEN_ENV) or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request_body = {
        "tool": "redmine",
        "method": method_name,
        "payload": dict(payload),
        "actor_context": {
            "actor_id": actor_id,
            "actor_role": actor_role,
        },
        "requested_at": _now_iso(),
    }

    try:
        with httpx.Client(timeout=resolved_timeout, verify=_resolve_live_verify_tls()) as client:
            response = client.post(endpoint, json=request_body, headers=headers)
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise IncidentAdapterError(f"redmine mcp live call failed: {exc}") from exc

    if response.status_code >= 400:
        body_excerpt = " ".join(response.text.split())[:240]
        raise IncidentAdapterError(
            f"redmine mcp live call failed with http {response.status_code}: {body_excerpt}"
        )

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise IncidentAdapterError("redmine mcp live response is not valid json") from exc

    return {
        "provider": "redmine_mcp",
        "mode": "live",
        "executed": True,
        "method": method_name,
        "endpoint": endpoint,
        "timeout_seconds": resolved_timeout,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "request_payload": dict(masked_payload),
        "response": _normalize_live_response(method_name, response_payload),
        "generated_at": _now_iso(),
    }


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

    Dry-run returns a simulated payload. Live mode uses an env-gated HTTP bridge for sandbox rehearsal.
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
        return _execute_live_redmine_action(
            method_name,
            payload,
            actor_id,
            actor_role,
            resolved_timeout,
            masked_payload,
        )

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
