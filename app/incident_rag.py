from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 3.0


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


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise IncidentAdapterError(f"{name} is required")
    return normalized


def fetch_knowledge_evidence(
    query: str,
    team: str,
    time_range: str,
    *,
    dry_run: bool | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """
    Stage 8 knowledge RAG adapter contract.

    Live calls are intentionally blocked at this phase; dry-run payloads are returned for pipeline integration.
    """
    query_text = _require_text("query", query)
    team_text = _require_text("team", team)
    range_text = _require_text("time_range", time_range)
    resolved_timeout = _resolve_timeout(timeout_seconds)

    if not _resolve_dry_run(dry_run):
        raise IncidentAdapterError("knowledge rag adapter is not configured for live mode")

    evidence_item = {
        "source": f"dryrun://knowledge/{team_text}",
        "summary": f"[dry-run] evidence for '{query_text}' within {range_text}",
        "confidence": 0.6,
        "timestamp": _now_iso(),
    }
    return {
        "provider": "knowledge_rag",
        "mode": "dry-run",
        "query": query_text,
        "team": team_text,
        "time_range": range_text,
        "timeout_seconds": resolved_timeout,
        "evidence": [evidence_item],
        "generated_at": _now_iso(),
    }


def fetch_system_signals(
    incident_id: str,
    service: str,
    window: str,
    *,
    dry_run: bool | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """
    Stage 8 system-analysis RAG adapter contract.

    Live calls are intentionally blocked at this phase; dry-run payloads are returned for pipeline integration.
    """
    incident = _require_text("incident_id", incident_id)
    service_name = _require_text("service", service)
    time_window = _require_text("window", window)
    resolved_timeout = _resolve_timeout(timeout_seconds)

    if not _resolve_dry_run(dry_run):
        raise IncidentAdapterError("system rag adapter is not configured for live mode")

    signal_item = {
        "symptom": f"[dry-run] latency/regression observed for {service_name}",
        "suspected_component": "unknown_component",
        "confidence": 0.55,
        "evidence_ref": f"dryrun://signals/{incident}",
    }
    return {
        "provider": "system_rag",
        "mode": "dry-run",
        "incident_id": incident,
        "service": service_name,
        "window": time_window,
        "timeout_seconds": resolved_timeout,
        "signals": [signal_item],
        "generated_at": _now_iso(),
    }
