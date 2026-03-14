from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent_planner import AgentPlanner
from app.auth import ActorContext, VALID_ROLES, actor_context_dependency
from app.incident_mcp import execute_redmine_action
from app.incident_policy import (
    IncidentPolicyDecision,
    POLICY_BLOCK_PATTERNS,
    detect_policy_block,
    evaluate_incident_action_policy,
    normalize_incident_risk_level,
    reason_message_for,
    requires_human_approval,
)
from app.incident_rag import fetch_knowledge_evidence, fetch_system_signals
from app.intent_classifier import IntentClassifier
from app.model_registry import load_model_registry, select_provider
from app.persistence import create_state_store
from app.provider_invoker import ProviderInvoker
from app.slack_adapter import execute_slack_action
from app.services import (
    ApprovalService,
    ApprovalServiceDeps,
    OrchestrationService,
    OrchestrationServiceDeps,
    ToolCatalogService,
    ToolCatalogServiceDeps,
    ToolDraftService,
    ToolDraftServiceDeps,
)
from app.tool_registry import (
    DEFAULT_TOOL_REGISTRY_OVERLAY_PATH,
    ToolRegistryError,
    compact_overlay_tool_registry,
    get_tool_capability,
    load_overlay_tool_registry,
    load_tool_registry,
    remove_tool_registry_tool,
    upsert_tool_registry_tool,
    validate_tool_capability,
)


class TaskStatus(str, Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    NEEDS_HUMAN_APPROVAL = "NEEDS_HUMAN_APPROVAL"
    DONE = "DONE"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    template_type: str = Field(min_length=1, max_length=100)
    input: dict[str, Any]
    requested_by: str = Field(min_length=1, max_length=100)


class RunTaskRequest(BaseModel):
    task_id: str = Field(min_length=1)
    idempotency_key: str | None = None
    run_mode: str = "standard"


class CreateIncidentRequest(BaseModel):
    incident_id: str = Field(min_length=1, max_length=120)
    service: str = Field(min_length=1, max_length=120)
    severity: IncidentSeverity
    detected_at: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=1000)
    time_window: str = Field(min_length=1, max_length=64)
    requested_by: str = Field(min_length=1, max_length=100)
    policy_profile: str = Field(min_length=1, max_length=100)
    dry_run: bool = True
    notify_channel: str | None = Field(default=None, max_length=120)


class RunIncidentRequest(BaseModel):
    task_id: str = Field(min_length=1)
    idempotency_key: str | None = None
    run_mode: str = "dry-run"


class AgentSubmitRequest(BaseModel):
    request_text: str = Field(min_length=1, max_length=4000)
    requested_by: str = Field(min_length=1, max_length=100)
    task_kind: str = Field(default="auto", min_length=4, max_length=16)
    title: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)
    auto_run: bool = True
    idempotency_key: str | None = None
    incident_run_mode: str = "dry-run"


class ApprovalDecisionRequest(BaseModel):
    acted_by: str = Field(min_length=1, max_length=100)
    comment: str | None = None


class CreateToolDraftRequest(BaseModel):
    requested_by: str = Field(min_length=1, max_length=100)
    request_text: str | None = Field(default=None, max_length=2000)
    tool_id: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    adapter: str | None = Field(default=None, max_length=100)
    method: str | None = Field(default=None, max_length=100)
    action_type: str | None = Field(default=None, max_length=120)
    external_system: str | None = Field(default=None, max_length=100)
    capability_family: str | None = Field(default=None, max_length=100)
    required_payload_fields: list[str] = Field(default_factory=list)
    default_risk_level: str = Field(default="medium", max_length=32)
    default_approval_required: bool = True
    supports_dry_run: bool = True


class ApplyToolDraftRequest(BaseModel):
    acted_by: str = Field(min_length=1, max_length=100)


APP = FastAPI(title="Local Work Delegation Orchestrator", version="0.1.0")
STATIC_ROOT = Path(__file__).resolve().parent / "static"
APP.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

STORE_LOCK = Lock()
STATE_STORE = create_state_store()
TASKS, TASK_EVENTS, APPROVAL_QUEUE, APPROVAL_ACTIONS, RUN_IDEMPOTENCY = STATE_STORE.load_state()

REPORTS_ROOT = Path("reports")
TOOL_DRAFTS_ROOT = Path("work/tool_drafts")
TOOL_REGISTRY_OVERLAY_PATH = DEFAULT_TOOL_REGISTRY_OVERLAY_PATH
TOOL_REGISTRY_HISTORY_ROOT = Path("work/tool_registry_history")
MAX_RETRY = 1

TEMPLATE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "meeting_summary": ("meeting_title", "meeting_date", "participants", "notes"),
}

TASK_WORKFLOW = "task"
INCIDENT_WORKFLOW = "incident"
INCIDENT_RUN_MODES = {"dry-run", "mcp-live", "live"}
AGENT_ENTRYPOINT = "agent"
SENSITIVE_TEXT_HINTS = ("internal only", "confidential", "sensitive", "민감", "내부 전용")
TASK_TICKET_HINTS = ("ticket", "issue", "follow-up", "follow up", "tracker", "redmine", "후속", "티켓", "이슈", "등록")
BINDING_SUMMARY_OUTPUT = "{{summary_output}}"
BINDING_SUMMARY_EXCERPT = "{{summary_excerpt}}"


def _build_incident_adapter_registry() -> dict[str, Any]:
    # Stage 8 skeleton binding point: keeps contracts importable before runtime integration.
    return {
        "knowledge_rag": fetch_knowledge_evidence,
        "system_rag": fetch_system_signals,
        "redmine_mcp": execute_redmine_action,
        "slack_api": execute_slack_action,
    }


INCIDENT_ADAPTERS = _build_incident_adapter_registry()
MODEL_REGISTRY = load_model_registry()
TOOL_REGISTRY = load_tool_registry()
PROVIDER_INVOKER = ProviderInvoker()
INTENT_CLASSIFIER = IntentClassifier(MODEL_REGISTRY)
TASK_PLANNER = AgentPlanner(MODEL_REGISTRY)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def _error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message, "request_id": f"req_{uuid4().hex[:10]}"}},
    )


def _log_event(task_id: str, event_type: str, **kwargs: Any) -> None:
    event = {
        "event_id": f"evt_{uuid4().hex[:12]}",
        "task_id": task_id,
        "event_type": event_type,
        "created_at": _now_iso(),
        **kwargs,
    }
    TASK_EVENTS.append(event)
    STATE_STORE.save_event(event)


def _persist_task(task: dict[str, Any]) -> None:
    STATE_STORE.save_task(task)


def _persist_approval(approval: dict[str, Any]) -> None:
    STATE_STORE.save_approval(approval)


def _persist_approval_action(action: dict[str, Any]) -> None:
    STATE_STORE.save_approval_action(action)


def _reload_tool_registry_runtime() -> None:
    global TOOL_REGISTRY
    TOOL_REGISTRY = load_tool_registry()
    TOOL_CATALOG_SERVICE.deps.registry = TOOL_REGISTRY


def _overlay_tool_snapshot(tool_id: str) -> dict[str, Any] | None:
    overlay = load_overlay_tool_registry(TOOL_REGISTRY_OVERLAY_PATH)
    if overlay is None:
        return None
    try:
        capability = get_tool_capability(overlay, tool_id)
    except ToolRegistryError:
        return None
    return capability.as_dict()


def _validate_tool_spec_for_registry(tool_spec: dict[str, Any]) -> dict[str, Any]:
    return validate_tool_capability(dict(tool_spec))


def _tool_registry_history_path(tool_id: str) -> Path:
    safe_tool_id = tool_id.replace(".", "_")
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return TOOL_REGISTRY_HISTORY_ROOT / f"{stamp}_{safe_tool_id}_{uuid4().hex[:6]}.json"


def _write_tool_registry_history(entry: dict[str, Any]) -> Path:
    TOOL_REGISTRY_HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    path = _tool_registry_history_path(str(entry.get("tool_id") or "tool"))
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _latest_tool_registry_apply_history(tool_id: str) -> tuple[dict[str, Any], Path]:
    normalized = tool_id.replace(".", "_")
    candidates = sorted(TOOL_REGISTRY_HISTORY_ROOT.glob(f"*_{normalized}_*.json"))
    for path in reversed(candidates):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if str(payload.get("action") or "") == "apply":
            return payload, path
    _error(404, "TOOL_HISTORY_NOT_FOUND", f"tool history not found: {tool_id}")


def _apply_tool_spec_to_registry(tool_spec: dict[str, Any], acted_by: str) -> dict[str, Any]:
    validation = _validate_tool_spec_for_registry(tool_spec)
    if not bool(validation.get("valid")):
        _error(400, "INVALID_TOOL_SPEC", f"tool spec failed validation: {tool_spec.get('tool_id')}")
    previous_overlay = _overlay_tool_snapshot(str(tool_spec.get("tool_id") or ""))
    capability = upsert_tool_registry_tool(TOOL_REGISTRY_OVERLAY_PATH, tool_spec)
    history_path = _write_tool_registry_history(
        {
            "action": "apply",
            "acted_by": acted_by,
            "applied_at": _now_iso(),
            "tool_id": capability.tool_id,
            "previous_overlay": previous_overlay,
            "applied_tool": capability.as_dict(),
        }
    )
    compaction = compact_overlay_tool_registry(overlay_path=TOOL_REGISTRY_OVERLAY_PATH)
    _reload_tool_registry_runtime()
    _log_event(
        "system_tool_registry",
        "TOOL_DRAFT_APPLIED",
        tool_id=capability.tool_id,
        adapter=capability.adapter,
        method=capability.method,
        acted_by=acted_by,
    )
    return {
        "tool": capability.as_dict(),
        "validation": validation,
        "history_path": str(history_path),
        "overlay_maintenance": compaction,
    }


def _rollback_tool_spec_in_registry(tool_id: str, acted_by: str) -> dict[str, Any]:
    normalized = str(tool_id or "").strip()
    if not normalized:
        _error(400, "INVALID_REQUEST", "tool_id is required")
    history_entry, history_path = _latest_tool_registry_apply_history(normalized)
    previous_overlay = history_entry.get("previous_overlay")
    restored_tool: dict[str, Any] | None = None
    action = "removed_overlay_tool"
    if isinstance(previous_overlay, dict) and previous_overlay.get("tool_id"):
        restored_capability = upsert_tool_registry_tool(TOOL_REGISTRY_OVERLAY_PATH, previous_overlay)
        restored_tool = restored_capability.as_dict()
        action = "restored_previous_overlay"
    else:
        removed = remove_tool_registry_tool(TOOL_REGISTRY_OVERLAY_PATH, normalized)
        if not removed:
            _error(409, "ROLLBACK_NOTHING_TO_DO", f"tool overlay not found for rollback: {normalized}")
    compaction = compact_overlay_tool_registry(overlay_path=TOOL_REGISTRY_OVERLAY_PATH)
    _reload_tool_registry_runtime()
    _log_event(
        "system_tool_registry",
        "TOOL_REGISTRY_ROLLED_BACK",
        tool_id=normalized,
        acted_by=acted_by,
        rollback_action=action,
    )
    return {
        "tool_id": normalized,
        "status": "ROLLED_BACK",
        "rollback_action": action,
        "restored_tool": restored_tool,
        "history_path": str(history_path),
        "overlay_maintenance": compaction,
    }


def _normalize_role(actor_role: str) -> str:
    role = actor_role.strip().lower()
    if role not in VALID_ROLES:
        _error(403, "FORBIDDEN", f"unsupported role: {actor_role}")
    return role


def _authorize(actor_role: str, allowed_roles: set[str], action: str) -> str:
    role = _normalize_role(actor_role)
    if role not in allowed_roles:
        _error(403, "FORBIDDEN", f"role '{role}' is not allowed for action: {action}")
    return role


def _authorize_task_access(
    task: dict[str, Any],
    actor_id: str,
    actor_role: str,
    *,
    allowed_roles: set[str],
    action: str,
) -> str:
    role = _authorize(actor_role, allowed_roles, action)
    if role == "requester" and task.get("requested_by") != actor_id:
        _error(403, "FORBIDDEN", "requester can only access their own task")
    return role


def _workflow_type(task: dict[str, Any]) -> str:
    return str(task.get("workflow_type") or TASK_WORKFLOW)


def _normalize_incident_run_mode(raw_mode: str | None) -> str:
    mode = str(raw_mode or "dry-run").strip().lower()
    if not mode:
        return "dry-run"
    if mode not in INCIDENT_RUN_MODES:
        _error(400, "INVALID_RUN_MODE", f"unsupported incident run_mode: {raw_mode}")
    return mode


def _incident_runtime_flags_for_mode(run_mode: str) -> tuple[bool, bool]:
    if run_mode == "live":
        return False, False
    if run_mode == "mcp-live":
        return True, False
    return True, True


def _incident_runtime_snapshot(runtime: dict[str, Any]) -> dict[str, Any]:
    if "context_dry_run" in runtime or "mcp_dry_run" in runtime:
        context_dry_run = bool(runtime.get("context_dry_run", True))
        mcp_dry_run = bool(runtime.get("mcp_dry_run", context_dry_run))
    else:
        dry_run = bool(runtime.get("dry_run", True))
        context_dry_run = dry_run
        mcp_dry_run = dry_run

    if context_dry_run and mcp_dry_run:
        run_mode = "dry-run"
    elif context_dry_run and not mcp_dry_run:
        run_mode = "mcp-live"
    elif not context_dry_run and not mcp_dry_run:
        run_mode = "live"
    else:
        run_mode = "mixed"

    return {
        "run_mode": run_mode,
        "context_dry_run": context_dry_run,
        "mcp_dry_run": mcp_dry_run,
        "dry_run": context_dry_run and mcp_dry_run,
    }


def _apply_incident_run_mode(runtime: dict[str, Any], run_mode: str | None) -> dict[str, Any]:
    normalized = _normalize_incident_run_mode(run_mode)
    context_dry_run, mcp_dry_run = _incident_runtime_flags_for_mode(normalized)
    runtime.update(
        {
            "run_mode": normalized,
            "context_dry_run": context_dry_run,
            "mcp_dry_run": mcp_dry_run,
            "dry_run": context_dry_run and mcp_dry_run,
        }
    )
    return runtime


def _ensure_workflow(task: dict[str, Any], expected: str, *, not_found_code: str, not_found_message: str) -> None:
    if _workflow_type(task) != expected:
        _error(404, not_found_code, not_found_message)


def _set_status(
    task: dict[str, Any],
    to_status: TaskStatus,
    *,
    reason_code: str | None = None,
    last_error: str | None = None,
    next_action: str | None = None,
    approval_queue_id: str | None = None,
    final_reason: str | None = None,
) -> None:
    from_status = task["status"]
    task["status"] = to_status.value
    task["updated_at"] = _now_iso()
    if reason_code is not None:
        task["approval_reason"] = reason_code
    if last_error is not None:
        task["last_error"] = last_error
    if next_action is not None:
        task["next_action"] = next_action
    if approval_queue_id is not None:
        task["approval_queue_id"] = approval_queue_id
    if final_reason is not None:
        task["final_reason"] = final_reason
    _persist_task(task)

    _log_event(
        task_id=task["task_id"],
        event_type="STATUS_CHANGED",
        from_status=from_status,
        to_status=to_status.value,
        reason_code=reason_code,
    )


def _set_stage(task: dict[str, Any], stage: str) -> None:
    task["current_stage"] = stage
    task["updated_at"] = _now_iso()
    _persist_task(task)
    _log_event(task["task_id"], "STAGE_CHANGED", stage=stage)


def _validate_task_input(template_type: str, payload: dict[str, Any]) -> None:
    if template_type not in TEMPLATE_REQUIRED_FIELDS:
        _error(400, "INVALID_REQUEST", f"unsupported template_type: {template_type}")
    required = TEMPLATE_REQUIRED_FIELDS[template_type]
    missing = [field for field in required if field not in payload or payload[field] in (None, "")]
    if missing:
        _error(400, "INVALID_REQUEST", f"missing required input fields: {', '.join(missing)}")


def _detect_policy_block(task_input: dict[str, Any], approved_reasons: set[str]) -> str | None:
    return detect_policy_block(task_input, approved_reasons, block_patterns=POLICY_BLOCK_PATTERNS)


def _incident_risk_level(task: dict[str, Any]) -> str:
    incident = task.get("incident") or {}
    return normalize_incident_risk_level(incident.get("severity") or IncidentSeverity.MEDIUM.value)


def _incident_requires_approval(risk_level: str) -> bool:
    return requires_human_approval(risk_level)


def _incident_summary(task: dict[str, Any]) -> str:
    incident = task.get("incident") or {}
    return str(incident.get("summary") or "").strip()


def _external_send_requested(task_input: dict[str, Any]) -> bool:
    return _detect_policy_block(task_input, set()) == "external_send_requested"


def _task_selection_context(task: dict[str, Any]) -> dict[str, Any]:
    task_input = dict(task.get("input") or {})
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    raw_sensitivity = str(metadata.get("sensitivity") or task_input.get("sensitivity") or "").strip().lower()
    notes_text = " ".join(
        str(item or "")
        for item in (
            task.get("title"),
            task_input.get("notes"),
            metadata.get("notes"),
        )
    ).lower()
    sensitivity = raw_sensitivity
    if sensitivity not in {"low", "high"}:
        sensitivity = "high" if any(token in notes_text for token in SENSITIVE_TEXT_HINTS) else "low"
    task_type = "summarize" if str(task.get("template_type") or "") == "meeting_summary" else str(task.get("template_type") or "general")
    return {
        "sensitivity": sensitivity,
        "task_type": task_type,
        "external_send": _external_send_requested(task_input),
    }


def _incident_selection_context(task: dict[str, Any]) -> dict[str, Any]:
    incident = dict(task.get("incident") or {})
    severity = str(incident.get("severity") or "").strip().lower()
    sensitivity = "high" if severity in {"high", "critical"} else "low"
    summary = str(incident.get("summary") or "").strip()
    return {
        "sensitivity": sensitivity,
        "task_type": "incident_response",
        "external_send": _external_send_requested({"summary": summary}),
    }


def _record_provider_selection(task: dict[str, Any], *, selection_context: dict[str, Any]) -> dict[str, Any]:
    selection = select_provider(
        MODEL_REGISTRY,
        sensitivity=str(selection_context.get("sensitivity") or "low"),
        task_type=str(selection_context.get("task_type") or "general"),
        external_send=bool(selection_context.get("external_send", False)),
    ).as_dict()
    task["provider_selection"] = selection
    task["updated_at"] = _now_iso()
    _persist_task(task)
    _log_event(
        task["task_id"],
        "MODEL_PROVIDER_SELECTED",
        provider_id=selection.get("provider_id"),
        provider_type=selection.get("provider_type"),
        engine=selection.get("engine"),
        model=selection.get("model"),
        selection_source=selection.get("selection_source"),
        sensitivity=selection.get("sensitivity"),
        task_type=selection.get("task_type"),
        external_send=selection.get("external_send"),
        requires_human_approval=selection.get("requires_human_approval"),
    )
    return selection


def _classify_agent_intent(request_text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return INTENT_CLASSIFIER.classify(request_text, metadata or {}).as_dict()


def _collect_incident_evidence(context: dict[str, Any]) -> list[str]:
    links: list[str] = []
    for item in context.get("knowledge", {}).get("evidence", []):
        source = str(item.get("source") or "").strip()
        if source:
            links.append(source)
    for item in context.get("system", {}).get("signals", []):
        source = str(item.get("evidence_ref") or "").strip()
        if source:
            links.append(source)
    return sorted(set(links))


def _incident_project_id() -> str:
    project_id = str(
        os.getenv("NEWCLAW_INCIDENT_PROJECT_ID")
        or os.getenv("NEWCLAW_STAGE8_SANDBOX_PROJECT")
        or "OPS"
    ).strip()
    return project_id or "OPS"


def _incident_ticket_tool_id() -> str:
    tool_id = str(os.getenv("NEWCLAW_INCIDENT_TICKET_TOOL_ID") or "redmine.issue.create").strip()
    return tool_id or "redmine.issue.create"


def _incident_slack_tool_id() -> str:
    tool_id = str(os.getenv("NEWCLAW_INCIDENT_SLACK_TOOL_ID") or "slack.message.send").strip()
    return tool_id or "slack.message.send"


def _task_slack_tool_id() -> str:
    tool_id = str(os.getenv("NEWCLAW_TASK_SLACK_TOOL_ID") or "slack.message.send").strip()
    return tool_id or "slack.message.send"


def _task_summary_tool_id() -> str:
    tool_id = str(os.getenv("NEWCLAW_TASK_SUMMARY_TOOL_ID") or "internal.summary.generate").strip()
    return tool_id or "internal.summary.generate"


def _task_ticket_tool_id() -> str:
    tool_id = str(os.getenv("NEWCLAW_TASK_TICKET_TOOL_ID") or "redmine.issue.create").strip()
    return tool_id or "redmine.issue.create"


def _is_truthy_value(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def _task_notify_channel(task: dict[str, Any]) -> str | None:
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    channel = str(metadata.get("notify_channel") or os.getenv("NEWCLAW_TASK_NOTIFY_CHANNEL") or "").strip()
    return channel or None


def _task_ticket_project_id(task: dict[str, Any]) -> str | None:
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    task_input = dict(task.get("input") or {})
    project_id = str(
        metadata.get("ticket_project_id")
        or metadata.get("project_id")
        or task_input.get("ticket_project_id")
        or task_input.get("project_id")
        or os.getenv("NEWCLAW_TASK_TICKET_PROJECT_ID")
        or ""
    ).strip()
    return project_id or None


def _task_ticket_requested(task: dict[str, Any]) -> bool:
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    for key in ("create_ticket", "followup_ticket", "ticket_required"):
        if _is_truthy_value(metadata.get(key)):
            return True
    haystack = " ".join(
        str(item or "")
        for item in (
            _task_request_text(task),
            metadata.get("ticket_subject"),
            metadata.get("notes"),
            dict(task.get("input") or {}).get("notes"),
        )
    ).lower()
    return any(token in haystack for token in TASK_TICKET_HINTS)


def _task_ticket_subject(task: dict[str, Any]) -> str:
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    task_input = dict(task.get("input") or {})
    subject = str(metadata.get("ticket_subject") or "").strip()
    if subject:
        return subject
    meeting_title = str(task_input.get("meeting_title") or task.get("title") or "Agent Request").strip()
    return f"[Follow-up] {meeting_title}"


def _task_ticket_priority(task: dict[str, Any]) -> str:
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    priority = str(metadata.get("ticket_priority") or "Normal").strip()
    return priority or "Normal"


def _task_ticket_description(task: dict[str, Any]) -> str:
    task_input = dict(task.get("input") or {})
    participants = task_input.get("participants") or []
    participant_text = ", ".join(str(item) for item in participants) if isinstance(participants, list) and participants else "N/A"
    return (
        "# Task Follow-up Request\n\n"
        f"- title: {task_input.get('meeting_title', task.get('title', 'Agent Request'))}\n"
        f"- date: {task_input.get('meeting_date', 'N/A')}\n"
        f"- requested_by: {task.get('requested_by', 'unknown')}\n"
        f"- participants: {participant_text}\n\n"
        "## Summary Output\n"
        f"{BINDING_SUMMARY_OUTPUT}\n\n"
        "## Notes\n"
        f"{task_input.get('notes', _task_request_text(task))}\n"
    )


def _task_planner_selection_context(task: dict[str, Any]) -> dict[str, Any]:
    context = _task_selection_context(task)
    context["task_type"] = "plan_actions"
    return context


def _task_request_text(task: dict[str, Any]) -> str:
    agent_request = dict(task.get("agent_request") or {})
    request_text = str(agent_request.get("request_text") or "").strip()
    if request_text:
        return request_text
    task_input = dict(task.get("input") or {})
    return str(task_input.get("notes") or task.get("title") or "").strip()


def _task_candidate_capabilities(task: dict[str, Any]) -> list[Any]:
    capabilities: list[Any] = []
    for item in _task_tool_eligibility(task):
        if not item["eligible"]:
            continue
        try:
            capabilities.append(get_tool_capability(TOOL_REGISTRY, str(item["tool_id"])))
        except ToolRegistryError as exc:
            raise RuntimeError(str(exc)) from exc
    return capabilities


def _task_tool_eligibility(task: dict[str, Any]) -> list[dict[str, Any]]:
    eligibility = [
        {
            "tool_id": _task_summary_tool_id(),
            "eligible": True,
            "reason": "always_required_summary",
        }
    ]
    notify_channel = _task_notify_channel(task)
    eligibility.append(
        {
            "tool_id": _task_slack_tool_id(),
            "eligible": bool(notify_channel),
            "reason": "notify_channel_available" if notify_channel else "notify_channel_missing",
        }
    )
    ticket_project_id = _task_ticket_project_id(task)
    ticket_requested = _task_ticket_requested(task)
    if ticket_project_id and ticket_requested:
        reason = "ticket_project_available_and_intent_detected"
        eligible = True
    elif not ticket_project_id:
        reason = "ticket_project_missing"
        eligible = False
    else:
        reason = "ticket_intent_missing"
        eligible = False
    eligibility.append(
        {
            "tool_id": _task_ticket_tool_id(),
            "eligible": eligible,
            "reason": reason,
        }
    )
    return eligibility


def _task_slack_message(task: dict[str, Any]) -> str:
    task_input = dict(task.get("input") or {})
    return (
        f"[NestClaw] {task_input.get('meeting_title', 'Agent Request')} "
        f"summary requested by {task.get('requested_by', 'unknown')}.\n\n"
        f"{BINDING_SUMMARY_EXCERPT}"
    )


def _task_payload_for_tool(
    task: dict[str, Any],
    capability: Any,
    payload_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_overrides = dict(payload_overrides or {})
    if capability.tool_id == _task_summary_tool_id():
        payload = dict(task.get("input") or {})
    elif capability.tool_id == _task_ticket_tool_id():
        payload = {
            "project_id": _task_ticket_project_id(task) or "",
            "subject": _task_ticket_subject(task),
            "description": _task_ticket_description(task),
            "priority": _task_ticket_priority(task),
        }
    elif capability.tool_id == _task_slack_tool_id():
        payload = {
            "channel": _task_notify_channel(task) or "",
            "text": _task_slack_message(task),
        }
    else:
        raise RuntimeError(f"unsupported task tool: {capability.tool_id}")
    payload.update(payload_overrides)
    for field_name in capability.required_payload_fields:
        value = payload.get(field_name)
        if value in (None, ""):
            raise RuntimeError(f"missing required field for {capability.tool_id}: {field_name}")
    return payload


def _task_planned_action(task: dict[str, Any], capability: Any, *, payload_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    execution_call = {
        "adapter": capability.adapter,
        "method": capability.method,
        "supports_dry_run": capability.supports_dry_run,
        "payload": _task_payload_for_tool(task, capability, payload_overrides),
    }
    return {
        "action_id": f"act_{uuid4().hex[:12]}",
        "title": capability.title,
        "action_type": capability.action_type,
        "tool_id": capability.tool_id,
        "tool_family": capability.capability_family,
        "external_system": capability.external_system,
        "risk_level": capability.default_risk_level,
        "approval_required": capability.default_approval_required,
        "tool_capability": capability.as_dict(),
        "execution_call": execution_call,
    }


def _build_task_planned_actions(task: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
    selection_context = _task_planner_selection_context(task)
    eligibility = _task_tool_eligibility(task)
    capabilities = _task_candidate_capabilities(task)
    decision = TASK_PLANNER.plan_task_actions(
        request_text=_task_request_text(task),
        task_input=dict(task.get("input") or {}),
        metadata=metadata,
        available_tools=capabilities,
        sensitivity=str(selection_context.get("sensitivity") or "low"),
        external_send=bool(selection_context.get("external_send", False)),
        eligibility=eligibility,
        default_notify_channel=_task_notify_channel(task),
    )
    capability_map = {item.tool_id: item for item in capabilities}
    planned_actions = [
        _task_planned_action(
            task,
            capability_map[action.tool_id],
            payload_overrides=dict(action.payload_overrides or {}),
        )
        for action in decision.actions
    ]
    provenance = decision.as_dict()
    return planned_actions, provenance


def _incident_notify_channel(task: dict[str, Any]) -> str | None:
    incident = dict(task.get("incident") or {})
    channel = str(incident.get("notify_channel") or os.getenv("NEWCLAW_INCIDENT_SLACK_CHANNEL") or "").strip()
    return channel or None


def _incident_tool_eligibility(task: dict[str, Any]) -> list[dict[str, Any]]:
    eligibility = [
        {
            "tool_id": _incident_ticket_tool_id(),
            "eligible": True,
            "reason": "incident_ticket_required",
        }
    ]
    notify_channel = _incident_notify_channel(task)
    eligibility.append(
        {
            "tool_id": _incident_slack_tool_id(),
            "eligible": bool(notify_channel),
            "reason": "notify_channel_available" if notify_channel else "notify_channel_missing",
        }
    )
    return eligibility


def _build_incident_planning_provenance(
    task: dict[str, Any],
    planned_actions: list[dict[str, Any]],
    eligibility: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "actions": [
            {
                "tool_id": str(item.get("tool_id") or ""),
                "reason": "incident_deterministic_baseline",
                "payload_overrides": {},
            }
            for item in planned_actions
        ],
        "source": "deterministic_incident_planner",
        "rationale": "incident workflow uses deterministic planner baseline before incident llm planner rollout",
        "confidence": 1.0,
        "provider_selection": dict(task.get("provider_selection") or {}),
        "eligible_tools": [dict(item) for item in eligibility],
        "fallback_reason": None,
        "degraded_mode": False,
    }


def _build_incident_planned_actions(task: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    incident = task.get("incident") or {}
    context = task.get("incident_context") or {}
    risk_level = _incident_risk_level(task)
    evidence_links = _collect_incident_evidence(context)
    summary = _incident_summary(task)
    eligibility = _incident_tool_eligibility(task)
    actions: list[dict[str, Any]] = []
    try:
        capability = get_tool_capability(TOOL_REGISTRY, _incident_ticket_tool_id())
    except ToolRegistryError as exc:
        raise RuntimeError(str(exc)) from exc

    payload: dict[str, Any] = {
        "project_id": _incident_project_id(),
        "subject": f"[INCIDENT] {incident.get('service', 'unknown-service')} {incident.get('severity', 'unknown')}",
        "description": summary,
        "priority": "High" if risk_level in {IncidentSeverity.HIGH.value, IncidentSeverity.CRITICAL.value} else "Normal",
    }
    if str(incident.get("source") or "").strip().lower() == "simulate_mcp_timeout":
        payload["simulate_timeout"] = True
    execution_call = {
        "adapter": capability.adapter,
        "method": capability.method,
        "supports_dry_run": capability.supports_dry_run,
        "payload": payload,
    }
    actions.append(
        {
            "action_id": f"act_{uuid4().hex[:12]}",
            "incident_id": incident.get("incident_id"),
            "title": capability.title,
            "action_type": capability.action_type,
            "tool_id": capability.tool_id,
            "tool_family": capability.capability_family,
            "external_system": capability.external_system,
            "risk_level": risk_level,
            "approval_required": capability.default_approval_required or _incident_requires_approval(risk_level),
            "evidence_links": evidence_links,
            "tool_capability": capability.as_dict(),
            "execution_call": execution_call,
            "mcp_call": dict(execution_call),
        }
    )

    notify_channel = _incident_notify_channel(task)
    if notify_channel:
        try:
            slack_capability = get_tool_capability(TOOL_REGISTRY, _incident_slack_tool_id())
        except ToolRegistryError as exc:
            raise RuntimeError(str(exc)) from exc
        slack_payload = {
            "channel": notify_channel,
            "text": (
                f"[Incident] {incident.get('service', 'unknown-service')} "
                f"severity={incident.get('severity', 'unknown')} "
                f"incident_id={incident.get('incident_id', 'N/A')} "
                f"summary={summary}"
            ),
        }
        slack_call = {
            "adapter": slack_capability.adapter,
            "method": slack_capability.method,
            "supports_dry_run": slack_capability.supports_dry_run,
            "payload": slack_payload,
        }
        actions.append(
            {
                "action_id": f"act_{uuid4().hex[:12]}",
                "incident_id": incident.get("incident_id"),
                "title": slack_capability.title,
                "action_type": slack_capability.action_type,
                "tool_id": slack_capability.tool_id,
                "tool_family": slack_capability.capability_family,
                "external_system": slack_capability.external_system,
                "risk_level": risk_level,
                "approval_required": slack_capability.default_approval_required or _incident_requires_approval(risk_level),
                "evidence_links": evidence_links,
                "tool_capability": slack_capability.as_dict(),
                "execution_call": slack_call,
                "mcp_call": dict(slack_call),
            }
        )

    return actions, _build_incident_planning_provenance(task, actions, eligibility)


def _build_incident_action_cards(task: dict[str, Any]) -> list[dict[str, Any]]:
    actions, _ = _build_incident_planned_actions(task)
    return actions


def _evaluate_incident_action_gate(
    task: dict[str, Any],
    action_card: dict[str, Any],
    approved_reasons: set[str],
) -> IncidentPolicyDecision:
    incident = task.get("incident") or {}
    return evaluate_incident_action_policy(
        action_card,
        summary=_incident_summary(task),
        approved_reasons=approved_reasons,
        policy_profile=str(incident.get("policy_profile") or "default"),
        block_patterns=POLICY_BLOCK_PATTERNS,
    )


def _extract_points(notes: str, limit: int = 5) -> list[str]:
    raw_lines = notes.replace("\r", "\n").split("\n")
    lines = [line.strip("-* \t") for line in raw_lines if line.strip()]
    if not lines and notes.strip():
        return [notes.strip()]
    return lines[:limit]


def _render_meeting_summary_from_input(payload: dict[str, Any]) -> str:
    points = _extract_points(str(payload["notes"]))
    if not points:
        raise ValueError("notes must include at least one meaningful line")

    participants = payload.get("participants", [])
    if not isinstance(participants, list):
        raise ValueError("participants must be a list")
    participant_text = ", ".join(str(item) for item in participants) if participants else "N/A"

    actions = []
    for idx, point in enumerate(points, start=1):
        actions.append(f"| Action {idx} | TBD | TBD | Medium | Open |")

    report = [
        "# 회의 결과 요약",
        "",
        f"- 회의 제목: {payload.get('meeting_title', 'N/A')}",
        f"- 회의 날짜: {payload.get('meeting_date', 'N/A')}",
        f"- 참석자: {participant_text}",
        "",
        "## 핵심 논점",
    ]
    report.extend([f"- {point}" for point in points])
    report.extend(
        [
            "",
            "## 액션 아이템",
            "| 항목 | 담당자 | 기한 | 우선순위 | 상태 |",
            "|---|---|---|---|---|",
            *actions,
            "",
            "## 확인 필요",
            "- 담당자/기한 확정 필요",
        ]
    )
    return "\n".join(report).strip() + "\n"


def _render_meeting_summary(task: dict[str, Any]) -> str:
    return _render_meeting_summary_from_input(dict(task["input"]))


def _create_approval_item(
    task: dict[str, Any],
    reason_code: str,
    *,
    reason_message: str | None = None,
    approver_group: str = "ops_team",
    review_recommendation: str | None = None,
) -> str:
    queue_id = f"aq_{uuid4().hex}"
    now = _now_iso()
    APPROVAL_QUEUE[queue_id] = {
        "queue_id": queue_id,
        "task_id": task["task_id"],
        "request_id": f"req_{uuid4().hex[:10]}",
        "reason_code": reason_code,
        "reason_message": reason_message or reason_message_for(reason_code),
        "requested_by": task["requested_by"],
        "approver_group": approver_group,
        "status": ApprovalStatus.PENDING.value,
        "created_at": now,
        "expires_at": None,
        "resolved_at": None,
    }
    if review_recommendation is not None:
        APPROVAL_QUEUE[queue_id]["review_recommendation"] = review_recommendation
    _persist_approval(APPROVAL_QUEUE[queue_id])
    _log_event(task["task_id"], "APPROVAL_REQUESTED", queue_id=queue_id, reason_code=reason_code)
    return queue_id


def _render_incident_report(task: dict[str, Any], action_results: list[dict[str, Any]]) -> str:
    incident = task.get("incident") or {}
    runtime_state = _incident_runtime_snapshot(dict(task.get("incident_runtime") or {}))
    lines = [
        "# Incident Orchestration Report",
        "",
        f"- incident_id: {incident.get('incident_id', 'N/A')}",
        f"- service: {incident.get('service', 'N/A')}",
        f"- severity: {incident.get('severity', 'N/A')}",
        f"- policy_profile: {incident.get('policy_profile', 'N/A')}",
        f"- run_mode: {runtime_state['run_mode']}",
        f"- context_dry_run: {runtime_state['context_dry_run']}",
        f"- mcp_dry_run: {runtime_state['mcp_dry_run']}",
        f"- dry_run: {runtime_state['dry_run']}",
        "",
        "## Action Results",
    ]
    if action_results:
        for item in action_results:
            lines.append(f"- {item.get('action_id')}: {item.get('status', 'unknown')}")
    else:
        lines.append("- no action executed")

    lines.extend(
        [
            "",
            "## Next Action",
            "- Continue monitoring and close when service metrics are stable.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _write_report(task_id: str, report_text: str, *, filename: str = "report.md") -> str:
    target = REPORTS_ROOT / task_id
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / filename
    report_path.write_text(report_text, encoding="utf-8")
    return str(report_path)


def _execution_call_for_action(planned_action: dict[str, Any]) -> dict[str, Any]:
    call = dict(planned_action.get("execution_call") or {})
    if call:
        return call
    return dict(planned_action.get("mcp_call") or {})


def _summary_binding_context(prior_results: list[dict[str, Any]] | None) -> dict[str, str]:
    summary_output = ""
    for item in prior_results or []:
        output_text = str(item.get("output_text") or "").strip()
        if output_text:
            summary_output = output_text
            break
    excerpt = summary_output[:280] if summary_output else ""
    return {
        BINDING_SUMMARY_OUTPUT: summary_output,
        BINDING_SUMMARY_EXCERPT: excerpt,
    }


def _apply_execution_bindings(value: Any, binding_context: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {str(key): _apply_execution_bindings(item, binding_context) for key, item in value.items()}
    if isinstance(value, list):
        return [_apply_execution_bindings(item, binding_context) for item in value]
    if isinstance(value, str):
        resolved = value
        for token, token_value in binding_context.items():
            resolved = resolved.replace(token, token_value)
        return resolved
    return value


def _dispatch_planned_action(
    task: dict[str, Any],
    planned_action: dict[str, Any],
    *,
    actor_context: dict[str, Any] | None = None,
    mcp_dry_run: bool = True,
    prior_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    task_id = str(task.get("task_id") or "")
    execution_call = _execution_call_for_action(planned_action)
    adapter_name = str(execution_call.get("adapter") or "").strip()
    method = str(execution_call.get("method") or "").strip()
    binding_context = _summary_binding_context(prior_results)
    payload = dict(_apply_execution_bindings(dict(execution_call.get("payload") or {}), binding_context))
    if bool(payload.get("simulate_timeout")):
        raise TimeoutError("simulated incident mcp timeout")

    if adapter_name == "provider_invoker":
        if method != "summary.generate":
            raise RuntimeError(f"unsupported provider_invoker method: {method}")
        summary_result = PROVIDER_INVOKER.invoke_meeting_summary(
            task_input=payload,
            provider_selection=dict(task.get("provider_selection") or {}),
            fallback_renderer=_render_meeting_summary_from_input,
        )
        invocation = summary_result.invocation.as_dict()
        _log_event(
            task_id,
            "MODEL_PROVIDER_INVOKED",
            provider_id=invocation.get("provider_id"),
            provider_type=invocation.get("provider_type"),
            engine=invocation.get("engine"),
            requested_model=invocation.get("requested_model"),
            resolved_model=invocation.get("resolved_model"),
            invoked=invocation.get("invoked"),
            result_source=invocation.get("result_source"),
            fallback_reason=invocation.get("fallback_reason"),
        )
        _log_event(
            task_id,
            "PLANNED_ACTION_EXECUTED",
            action_id=planned_action.get("action_id"),
            tool_id=planned_action.get("tool_id"),
            adapter=adapter_name,
            method=method,
            mode=invocation.get("result_source"),
        )
        return {
            "action_id": planned_action.get("action_id"),
            "status": "generated",
            "tool_id": planned_action.get("tool_id"),
            "adapter": adapter_name,
            "method": method,
            "mode": invocation.get("result_source"),
            "provider_invocation": invocation,
            "request_payload": dict(payload),
            "output_text": summary_result.output_text,
        }

    adapter = INCIDENT_ADAPTERS.get(adapter_name)
    if adapter is None:
        raise RuntimeError(f"incident adapter not found: {adapter_name}")
    action_actor_context = dict(actor_context or {"actor_id": task.get("requested_by"), "actor_role": "requester"})
    mcp_result = adapter(
        method=method,
        payload=payload,
        actor_context=action_actor_context,
        dry_run=mcp_dry_run,
        timeout_seconds=3.0,
    )
    result = {
        "action_id": planned_action.get("action_id"),
        "status": "dry-run" if mcp_dry_run else "executed",
        "tool_id": planned_action.get("tool_id"),
        "adapter": adapter_name,
        "method": method,
        "mode": mcp_result.get("mode"),
        "external_ref": mcp_result.get("response", {}).get("external_ref"),
        "request_payload": dict(mcp_result.get("request_payload") or payload),
    }
    _log_event(
        task_id,
        "INCIDENT_ACTION_EXECUTED",
        action_id=planned_action.get("action_id"),
        tool_id=planned_action.get("tool_id"),
        adapter=adapter_name,
        method=method,
        mode=mcp_result.get("mode"),
        external_ref=mcp_result.get("response", {}).get("external_ref"),
    )
    _log_event(
        task_id,
        "PLANNED_ACTION_EXECUTED",
        action_id=planned_action.get("action_id"),
        tool_id=planned_action.get("tool_id"),
        adapter=adapter_name,
        method=method,
        mode=mcp_result.get("mode"),
    )
    return result


def _execute_once(task_id: str) -> bool:
    # Returns True when execution completed (DONE). False when it moved to approval.
    with STORE_LOCK:
        task = TASKS.get(task_id)
        if not task:
            return True
        if _workflow_type(task) != TASK_WORKFLOW:
            return True
        if task["status"] != TaskStatus.RUNNING.value:
            return True
        _set_stage(task, "planner")

    with STORE_LOCK:
        task = TASKS[task_id]
        _record_provider_selection(task, selection_context=_task_selection_context(task))
        planned_actions, planning_provenance = _build_task_planned_actions(task)
        task["planned_actions"] = planned_actions
        task["planning_provenance"] = planning_provenance
        task["updated_at"] = _now_iso()
        _persist_task(task)
        planner_selection = dict(planning_provenance.get("provider_selection") or {})
        if planning_provenance.get("fallback_reason"):
            _log_event(
                task_id,
                "TASK_PLAN_FALLBACK",
                source=planning_provenance.get("source"),
                fallback_reason=planning_provenance.get("fallback_reason"),
            )
        _log_event(
            task_id,
            "TASK_PLAN_GENERATED",
            source=planning_provenance.get("source"),
            confidence=planning_provenance.get("confidence"),
            degraded_mode=planning_provenance.get("degraded_mode"),
            provider_id=planner_selection.get("provider_id"),
            provider_type=planner_selection.get("provider_type"),
            engine=planner_selection.get("engine"),
            model=planner_selection.get("model"),
            action_count=len(planned_actions),
            selected_tools=",".join(str(item.get("tool_id") or "") for item in planned_actions),
        )
        _log_event(task_id, "TASK_ACTIONS_PLANNED", count=len(planned_actions))
        _log_event(task_id, "PLANNED_ACTIONS_BUILT", count=len(planned_actions))
        _set_stage(task, "executor")
        approved_reasons = set(task.get("approved_reasons", []))
        reason_code = _detect_policy_block(task["input"], approved_reasons)
        if reason_code:
            _log_event(task["task_id"], "BLOCKED_POLICY", reason_code=reason_code)
            queue_id = _create_approval_item(task, reason_code)
            _set_status(
                task,
                TaskStatus.NEEDS_HUMAN_APPROVAL,
                reason_code=reason_code,
                next_action="approve_or_reject",
                approval_queue_id=queue_id,
            )
            return False

    with STORE_LOCK:
        task = dict(TASKS[task_id])
        template_type = task["template_type"]
        if template_type != "meeting_summary":
            raise ValueError(f"unsupported template_type at runtime: {template_type}")
        planned_actions = list(task.get("planned_actions") or [])

    action_results: list[dict[str, Any]] = []
    for planned_action in planned_actions:
        action_results.append(_dispatch_planned_action(task, planned_action, prior_results=action_results))
    summary_result = action_results[0]
    report_text = str(summary_result["output_text"])

    report_path = _write_report(task_id, report_text)

    with STORE_LOCK:
        task = TASKS[task_id]
        invocation = dict(summary_result.get("provider_invocation") or {})
        task["provider_invocation"] = invocation
        task["action_results"] = [{key: value for key, value in item.items() if key != "output_text"} for item in action_results]
        task["updated_at"] = _now_iso()
        _persist_task(task)
        _set_stage(task, "reviewer")
        if "# 회의 결과 요약" not in report_text:
            raise ValueError("review failed: report header missing")

        _set_stage(task, "reporter")
        task["result"] = {
            "report_path": report_path,
            "provider_invocation": invocation,
            "actions_executed": len(action_results),
        }
        task["completed_at"] = _now_iso()
        _set_status(task, TaskStatus.DONE, next_action="none")
    return True


def _execute_incident_once(task_id: str) -> bool:
    # Returns True when execution completed (DONE). False when it moved to approval.
    with STORE_LOCK:
        task = TASKS.get(task_id)
        if not task:
            return True
        if _workflow_type(task) != INCIDENT_WORKFLOW:
            return True
        if task["status"] != TaskStatus.RUNNING.value:
            return True
        _set_stage(task, "ingest")
        incident = dict(task.get("incident") or {})
        runtime = dict(task.get("incident_runtime") or {})
        approved_reasons = set(task.get("approved_reasons", []))

    with STORE_LOCK:
        task = TASKS[task_id]
        _set_stage(task, "planner")

    runtime_state = _incident_runtime_snapshot(runtime)
    context_dry_run = bool(runtime_state["context_dry_run"])
    mcp_dry_run = bool(runtime_state["mcp_dry_run"])
    knowledge = INCIDENT_ADAPTERS["knowledge_rag"](
        query=f"{incident.get('service', 'unknown-service')} {incident.get('summary', '')}".strip(),
        team="platform",
        time_range="90d",
        dry_run=context_dry_run,
        timeout_seconds=3.0,
    )
    system = INCIDENT_ADAPTERS["system_rag"](
        incident_id=str(incident.get("incident_id") or ""),
        service=str(incident.get("service") or ""),
        window=str(incident.get("time_window") or "15m"),
        dry_run=context_dry_run,
        timeout_seconds=3.0,
    )
    context = {"knowledge": knowledge, "system": system}

    with STORE_LOCK:
        task = TASKS[task_id]
        _record_provider_selection(task, selection_context=_incident_selection_context(task))
        task["incident_context"] = context
        task["updated_at"] = _now_iso()
        _persist_task(task)
        _log_event(
            task_id,
            "INCIDENT_CONTEXT_BUILT",
            evidence_count=len(knowledge.get("evidence", [])),
            signal_count=len(system.get("signals", [])),
        )
        planned_actions, planning_provenance = _build_incident_planned_actions(task)
        action_cards = planned_actions
        task["action_cards"] = action_cards
        task["planned_actions"] = planned_actions
        task["planning_provenance"] = planning_provenance
        task["updated_at"] = _now_iso()
        _persist_task(task)
        planner_selection = dict(planning_provenance.get("provider_selection") or {})
        _log_event(
            task_id,
            "INCIDENT_PLAN_GENERATED",
            source=planning_provenance.get("source"),
            confidence=planning_provenance.get("confidence"),
            degraded_mode=planning_provenance.get("degraded_mode"),
            provider_id=planner_selection.get("provider_id"),
            provider_type=planner_selection.get("provider_type"),
            engine=planner_selection.get("engine"),
            model=planner_selection.get("model"),
            action_count=len(planned_actions),
            selected_tools=",".join(str(item.get("tool_id") or "") for item in planned_actions),
        )
        _log_event(task_id, "INCIDENT_ACTIONS_PLANNED", count=len(action_cards))
        _log_event(task_id, "PLANNED_ACTIONS_BUILT", count=len(action_cards))
        _set_stage(task, "executor")

        for action_card in action_cards:
            decision = _evaluate_incident_action_gate(task, action_card, approved_reasons)
            if decision.gate_status == "BLOCKED_POLICY":
                _log_event(
                    task_id,
                    "BLOCKED_POLICY",
                    reason_code=decision.reason_code,
                    action_id=action_card.get("action_id"),
                    review_recommendation=decision.review_recommendation,
                )
                queue_id = _create_approval_item(
                    task,
                    str(decision.reason_code),
                    reason_message=decision.reason_message,
                    approver_group=decision.approver_group,
                    review_recommendation=decision.review_recommendation,
                )
                _set_status(
                    task,
                    TaskStatus.NEEDS_HUMAN_APPROVAL,
                    reason_code=decision.reason_code,
                    next_action="approve_or_reject",
                    approval_queue_id=queue_id,
                )
                return False
            if decision.gate_status == "NEEDS_APPROVAL":
                queue_id = _create_approval_item(
                    task,
                    str(decision.reason_code),
                    reason_message=decision.reason_message,
                    approver_group=decision.approver_group,
                    review_recommendation=decision.review_recommendation,
                )
                _set_status(
                    task,
                    TaskStatus.NEEDS_HUMAN_APPROVAL,
                    reason_code=decision.reason_code,
                    next_action="approve_or_reject",
                    approval_queue_id=queue_id,
                )
                _log_event(
                    task_id,
                    "INCIDENT_APPROVAL_QUEUED",
                    action_id=action_card.get("action_id"),
                    reason_code=decision.reason_code,
                    review_recommendation=decision.review_recommendation,
                )
                return False

        actor_context = {
            "actor_id": task.get("requested_by"),
            "actor_role": "requester",
        }

    action_results: list[dict[str, Any]] = []
    for action_card in action_cards:
        action_results.append(
            _dispatch_planned_action(
                task,
                action_card,
                actor_context=actor_context,
                mcp_dry_run=mcp_dry_run,
                prior_results=action_results,
            )
        )

    with STORE_LOCK:
        task = TASKS[task_id]
        task["action_results"] = action_results
        task["updated_at"] = _now_iso()
        _persist_task(task)
        report_text = _render_incident_report(task, action_results)
        _set_stage(task, "reviewer")
        if "# Incident Orchestration Report" not in report_text:
            raise ValueError("incident review failed: report header missing")
        _set_stage(task, "reporter")

    report_path = _write_report(task_id, report_text, filename="incident_report.md")

    with STORE_LOCK:
        task = TASKS[task_id]
        task["result"] = {
            "report_path": report_path,
            "actions_executed": len(action_results),
            "remaining_risk": "human_review_recommended",
            "next_action": "monitor_service",
        }
        task["completed_at"] = _now_iso()
        _set_status(task, TaskStatus.DONE, next_action="none")
    return True


def _run_pipeline(task_id: str) -> None:
    while True:
        try:
            completed = _execute_once(task_id)
            if completed:
                return
            return
        except Exception as exc:
            with STORE_LOCK:
                task = TASKS.get(task_id)
                if not task:
                    return
                retry_count = int(task.get("retry_count", 0))
                if retry_count < MAX_RETRY:
                    task["retry_count"] = retry_count + 1
                    _set_status(
                        task,
                        TaskStatus.FAILED_RETRYABLE,
                        last_error=str(exc),
                        next_action="retrying",
                    )
                    _log_event(task_id, "RETRY_STARTED", retry_count=task["retry_count"])
                    _set_status(task, TaskStatus.RUNNING, next_action="wait_for_completion")
                    continue

                queue_id = _create_approval_item(task, "retry_exhausted")
                _set_status(
                    task,
                    TaskStatus.NEEDS_HUMAN_APPROVAL,
                    reason_code="retry_exhausted",
                    last_error=str(exc),
                    next_action="approve_or_reject",
                    approval_queue_id=queue_id,
                )
                return


def _run_incident_pipeline(task_id: str) -> None:
    while True:
        try:
            completed = _execute_incident_once(task_id)
            if completed:
                return
            return
        except Exception as exc:
            with STORE_LOCK:
                task = TASKS.get(task_id)
                if not task:
                    return
                if _workflow_type(task) != INCIDENT_WORKFLOW:
                    return
                retry_count = int(task.get("retry_count", 0))
                if retry_count < MAX_RETRY:
                    task["retry_count"] = retry_count + 1
                    _set_status(
                        task,
                        TaskStatus.FAILED_RETRYABLE,
                        last_error=str(exc),
                        next_action="retrying",
                    )
                    _log_event(task_id, "RETRY_STARTED", retry_count=task["retry_count"])
                    _set_status(task, TaskStatus.RUNNING, next_action="wait_for_completion")
                    continue

                queue_id = _create_approval_item(task, "retry_exhausted")
                _set_status(
                    task,
                    TaskStatus.NEEDS_HUMAN_APPROVAL,
                    reason_code="retry_exhausted",
                    last_error=str(exc),
                    next_action="approve_or_reject",
                    approval_queue_id=queue_id,
                )
                return


def _start_pipeline(task_id: str) -> None:
    worker = Thread(target=_run_pipeline, args=(task_id,), daemon=True)
    worker.start()


def _start_incident_pipeline(task_id: str) -> None:
    worker = Thread(target=_run_incident_pipeline, args=(task_id,), daemon=True)
    worker.start()


def _start_pipeline_for_workflow(task: dict[str, Any]) -> None:
    workflow = _workflow_type(task)
    if workflow == INCIDENT_WORKFLOW:
        _start_incident_pipeline(task["task_id"])
        return
    _start_pipeline(task["task_id"])


def _run_pipeline_for_workflow_sync(task: dict[str, Any]) -> None:
    workflow = _workflow_type(task)
    if workflow == INCIDENT_WORKFLOW:
        _run_incident_pipeline(task["task_id"])
        return
    _run_pipeline(task["task_id"])


def build_orchestration_service(*, sync_execution: bool = False) -> OrchestrationService:
    return OrchestrationService(
        OrchestrationServiceDeps(
            store_lock=STORE_LOCK,
            tasks=TASKS,
            task_events=TASK_EVENTS,
            run_idempotency=RUN_IDEMPOTENCY,
            state_store=STATE_STORE,
            reports_root=REPORTS_ROOT,
            task_workflow=TASK_WORKFLOW,
            incident_workflow=INCIDENT_WORKFLOW,
            agent_entrypoint=AGENT_ENTRYPOINT,
            task_status_ready=TaskStatus.READY,
            task_status_running=TaskStatus.RUNNING,
            task_status_failed_retryable=TaskStatus.FAILED_RETRYABLE,
            task_status_needs_human_approval=TaskStatus.NEEDS_HUMAN_APPROVAL,
            task_status_done=TaskStatus.DONE,
            now_iso=_now_iso,
            error=_error,
            authorize=_authorize,
            authorize_task_access=_authorize_task_access,
            ensure_workflow=_ensure_workflow,
            validate_task_input=_validate_task_input,
            set_status=_set_status,
            workflow_type=_workflow_type,
            apply_incident_run_mode=_apply_incident_run_mode,
            incident_runtime_snapshot=_incident_runtime_snapshot,
            normalize_incident_run_mode=_normalize_incident_run_mode,
            classify_agent_intent=_classify_agent_intent,
            start_pipeline=_run_pipeline if sync_execution else _start_pipeline,
            start_incident_pipeline=_run_incident_pipeline if sync_execution else _start_incident_pipeline,
            persist_task=_persist_task,
            log_event=_log_event,
        )
    )


def build_approval_service(*, sync_execution: bool = False) -> ApprovalService:
    return ApprovalService(
        ApprovalServiceDeps(
            store_lock=STORE_LOCK,
            tasks=TASKS,
            approval_queue=APPROVAL_QUEUE,
            approval_actions=APPROVAL_ACTIONS,
            approval_status_pending=ApprovalStatus.PENDING.value,
            approval_status_approved=ApprovalStatus.APPROVED.value,
            approval_status_rejected=ApprovalStatus.REJECTED.value,
            task_status_running=TaskStatus.RUNNING,
            task_status_done=TaskStatus.DONE,
            now_iso=_now_iso,
            error=_error,
            authorize=_authorize,
            persist_approval=_persist_approval,
            persist_approval_action=_persist_approval_action,
            set_status=_set_status,
            log_event=_log_event,
            start_pipeline_for_workflow=_run_pipeline_for_workflow_sync if sync_execution else _start_pipeline_for_workflow,
        )
    )


def build_tool_catalog_service() -> ToolCatalogService:
    return ToolCatalogService(
        ToolCatalogServiceDeps(
            registry=TOOL_REGISTRY,
            authorize=_authorize,
            error=_error,
        )
    )


def build_tool_draft_service() -> ToolDraftService:
    return ToolDraftService(
        ToolDraftServiceDeps(
            authorize=_authorize,
            error=_error,
            now_iso=_now_iso,
            drafts_root=TOOL_DRAFTS_ROOT,
            validate_tool_spec=_validate_tool_spec_for_registry,
            apply_tool_spec=_apply_tool_spec_to_registry,
            rollback_tool=_rollback_tool_spec_in_registry,
        )
    )


ORCHESTRATION_SERVICE = build_orchestration_service(sync_execution=False)
APPROVAL_SERVICE = build_approval_service(sync_execution=False)
TOOL_CATALOG_SERVICE = build_tool_catalog_service()
TOOL_DRAFT_SERVICE = build_tool_draft_service()


@APP.get("/", include_in_schema=False)
def quickstart_console() -> FileResponse:
    return FileResponse(STATIC_ROOT / "agent-quickstart.html")


@APP.get("/console", include_in_schema=False)
def web_console() -> FileResponse:
    return FileResponse(STATIC_ROOT / "agent-console.html")


@APP.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@APP.post("/api/v1/agent/submit", status_code=202)
def agent_submit(
    req: AgentSubmitRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.submit_agent(req, actor)


@APP.get("/api/v1/agent/status/{task_id}")
def agent_status(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.agent_status(task_id, actor)


@APP.get("/api/v1/agent/events/{task_id}")
def agent_events(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.agent_events(task_id, actor)


@APP.get("/api/v1/agent/recent")
def agent_recent(
    limit: int = Query(default=10, ge=1, le=50),
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.agent_recent(actor, limit=limit)


@APP.get("/api/v1/agent/report/{task_id}")
def agent_report(
    task_id: str,
    max_chars: int = Query(default=4000, ge=200, le=20000),
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.agent_report(task_id, actor, max_chars=max_chars)


@APP.get("/api/v1/agent/report/{task_id}/raw")
def agent_report_raw(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> FileResponse:
    return FileResponse(ORCHESTRATION_SERVICE.agent_report_path(task_id, actor), media_type="text/markdown")


@APP.get("/api/v1/tools")
def list_tools(
    capability_family: str | None = Query(default=None),
    external_system: str | None = Query(default=None),
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_CATALOG_SERVICE.list_tools(capability_family, external_system, actor)


@APP.get("/api/v1/tools/{tool_id}")
def get_tool(
    tool_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_CATALOG_SERVICE.get_tool(tool_id, actor)


@APP.post("/api/v1/tool-drafts", status_code=201)
def create_tool_draft(
    req: CreateToolDraftRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_DRAFT_SERVICE.create_draft(req, actor)


@APP.get("/api/v1/tool-drafts/{draft_id}")
def get_tool_draft(
    draft_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_DRAFT_SERVICE.get_draft(draft_id, actor)


@APP.get("/api/v1/tool-drafts/{draft_id}/validate")
def validate_tool_draft(
    draft_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_DRAFT_SERVICE.validate_draft(draft_id, actor)


@APP.post("/api/v1/tool-drafts/{draft_id}/apply")
def apply_tool_draft(
    draft_id: str,
    req: ApplyToolDraftRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_DRAFT_SERVICE.apply_draft(draft_id, req, actor)


@APP.post("/api/v1/tools/{tool_id}/rollback")
def rollback_tool(
    tool_id: str,
    req: ApplyToolDraftRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return TOOL_DRAFT_SERVICE.rollback_tool(tool_id, req, actor)


@APP.post("/api/v1/task/create", status_code=201)
def create_task(
    req: CreateTaskRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.create_task(req, actor)


@APP.post("/api/v1/task/run", status_code=202)
def run_task(
    req: RunTaskRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.run_task(req, actor)


@APP.get("/api/v1/task/status/{task_id}")
def task_status(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.task_status(task_id, actor)


@APP.get("/api/v1/task/events/{task_id}")
def task_events(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.task_events(task_id, actor)


@APP.post("/api/v1/incident/create", status_code=201)
def create_incident(
    req: CreateIncidentRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.create_incident(req, actor)


@APP.post("/api/v1/incident/run", status_code=202)
def run_incident(
    req: RunIncidentRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.run_incident(req, actor)


@APP.get("/api/v1/incident/status/{task_id}")
def incident_status(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.incident_status(task_id, actor)


@APP.get("/api/v1/incident/events/{task_id}")
def incident_events(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return ORCHESTRATION_SERVICE.incident_events(task_id, actor)


@APP.get("/api/v1/approvals")
def list_approvals(
    status: str | None = Query(default=None),
    approver_group: str | None = Query(default=None),
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return APPROVAL_SERVICE.list_approvals(status, approver_group, actor)


@APP.get("/api/v1/approvals/{queue_id}")
def get_approval(
    queue_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return APPROVAL_SERVICE.get_approval(queue_id, actor)


@APP.post("/api/v1/approvals/{queue_id}/approve")
def approve_queue_item(
    queue_id: str,
    req: ApprovalDecisionRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return APPROVAL_SERVICE.approve(queue_id, req, actor)


@APP.post("/api/v1/approvals/{queue_id}/reject")
def reject_queue_item(
    queue_id: str,
    req: ApprovalDecisionRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    return APPROVAL_SERVICE.reject(queue_id, req, actor)


@APP.get("/api/v1/audit/summary")
def audit_summary(actor: ActorContext = Depends(actor_context_dependency)) -> dict[str, Any]:
    _authorize(actor.actor_role, {"reviewer", "admin"}, "audit_summary")
    with STORE_LOCK:
        blocked_policy = sum(1 for event in TASK_EVENTS if event.get("event_type") == "BLOCKED_POLICY")
        approvals_pending = sum(1 for item in APPROVAL_QUEUE.values() if item.get("status") == ApprovalStatus.PENDING.value)
        approvals_resolved = sum(
            1
            for item in APPROVAL_QUEUE.values()
            if item.get("status") in {ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value}
        )
        return {
            "total_events": len(TASK_EVENTS),
            "blocked_policy_events": blocked_policy,
            "policy_bypass_events": 0,
            "approvals_pending": approvals_pending,
            "approvals_resolved": approvals_resolved,
        }
