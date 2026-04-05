from __future__ import annotations

from typing import Any, Mapping, Sequence


POLICY_BLOCK_REASON_CODES = {"external_send_requested"}
APPROVAL_PENDING_REASON_CODES = {"missing_evidence", "high_risk_action", "critical_risk_action"}
RETRYABLE_REASON_CODES = {"retry_exhausted"}


def readiness_state_summary(missing_env: Sequence[str]) -> dict[str, Any]:
    missing = [str(item).strip() for item in missing_env if str(item).strip()]
    if missing:
        return {
            "status": "blocked",
            "canonical_state": "blocked",
            "canonical_reason_code": "env_blocked",
            "detail_reason_code": "stage8_live_env_missing",
            "message": "stage8 live readiness is blocked by missing external environment inputs",
            "missing_env": missing,
        }
    return {
        "status": "ready",
        "canonical_state": "ready",
        "canonical_reason_code": "ready",
        "detail_reason_code": None,
        "message": "stage8 live readiness prerequisites are present",
        "missing_env": [],
    }


def runtime_state_summary(
    task: Mapping[str, Any],
    *,
    ready_status: str,
    running_status: str,
    failed_retryable_status: str,
    needs_human_approval_status: str,
    done_status: str,
) -> dict[str, Any]:
    status = str(task.get("status") or "")
    planning = dict(task.get("planning_provenance") or {})
    approval_reason = _optional_text(task.get("approval_reason"))
    fallback_reason = _optional_text(planning.get("fallback_reason"))
    final_reason = _optional_text(task.get("final_reason"))
    last_error = _optional_text(task.get("last_error"))
    degraded = bool(planning.get("degraded_mode"))

    canonical_state = "unknown"
    canonical_reason_code = "unknown"
    detail_reason_code: str | None = None
    message = "runtime state is not yet classified"

    if status == ready_status:
        canonical_state = "ready"
        canonical_reason_code = "ready"
        message = "task is ready for execution"
    elif status == running_status:
        canonical_state = "running"
        canonical_reason_code = "planner_degraded" if degraded else "running"
        detail_reason_code = fallback_reason
        message = (
            "task is running with planner fallback"
            if degraded
            else "task is currently running"
        )
    elif status == failed_retryable_status:
        canonical_state = "retryable_failure"
        canonical_reason_code = "retryable_failure"
        detail_reason_code = _detail_from_error(last_error)
        message = "task hit a retryable execution failure"
    elif status == needs_human_approval_status:
        canonical_state = "approval_pending"
        detail_reason_code = approval_reason
        if approval_reason in POLICY_BLOCK_REASON_CODES:
            canonical_reason_code = "policy_blocked"
            message = "task is waiting on policy review before continuing"
        elif approval_reason in RETRYABLE_REASON_CODES:
            canonical_reason_code = "retryable_failure"
            message = "task exhausted retries and now needs human approval"
        else:
            canonical_reason_code = "approval_pending"
            message = "task is waiting on human approval"
    elif status == done_status:
        canonical_state = "done"
        canonical_reason_code = "planner_degraded" if degraded else "completed"
        detail_reason_code = fallback_reason or final_reason
        message = (
            "task completed after planner fallback"
            if degraded
            else "task completed successfully"
        )

    return {
        "canonical_state": canonical_state,
        "canonical_reason_code": canonical_reason_code,
        "detail_reason_code": detail_reason_code,
        "message": message,
        "degraded": degraded,
        "fallback_reason": fallback_reason,
        "last_error": last_error,
    }


def _detail_from_error(last_error: str | None) -> str | None:
    if not last_error:
        return None
    lowered = last_error.lower()
    if "timeout" in lowered:
        return "timeout"
    if "connection" in lowered:
        return "connection_error"
    if "not found" in lowered:
        return "not_found"
    return "execution_error"


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
