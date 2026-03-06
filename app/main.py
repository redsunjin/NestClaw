from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import ActorContext, VALID_ROLES, actor_context_dependency
from app.incident_mcp import execute_redmine_action
from app.incident_rag import fetch_knowledge_evidence, fetch_system_signals
from app.persistence import create_state_store


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


class RunIncidentRequest(BaseModel):
    task_id: str = Field(min_length=1)
    idempotency_key: str | None = None
    run_mode: str = "dry-run"


class ApprovalDecisionRequest(BaseModel):
    acted_by: str = Field(min_length=1, max_length=100)
    comment: str | None = None


APP = FastAPI(title="Local Work Delegation Orchestrator", version="0.1.0")

STORE_LOCK = Lock()
STATE_STORE = create_state_store()
TASKS, TASK_EVENTS, APPROVAL_QUEUE, APPROVAL_ACTIONS, RUN_IDEMPOTENCY = STATE_STORE.load_state()

REPORTS_ROOT = Path("reports")
MAX_RETRY = 1

TEMPLATE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "meeting_summary": ("meeting_title", "meeting_date", "participants", "notes"),
}

POLICY_BLOCK_PATTERNS: dict[str, tuple[str, ...]] = {
    "external_send_requested": (
        "외부 전송",
        "external send",
        "메일 발송",
        "send externally",
        "http://",
        "https://",
    )
}

TASK_WORKFLOW = "task"
INCIDENT_WORKFLOW = "incident"
INCIDENT_RISK_APPROVAL_REQUIRED = {"high", "critical"}


def _build_incident_adapter_registry() -> dict[str, Any]:
    # Stage 8 skeleton binding point: keeps contracts importable before runtime integration.
    return {
        "knowledge_rag": fetch_knowledge_evidence,
        "system_rag": fetch_system_signals,
        "redmine_mcp": execute_redmine_action,
    }


INCIDENT_ADAPTERS = _build_incident_adapter_registry()


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
    joined = " ".join(str(value) for value in task_input.values()).lower()
    for reason_code, patterns in POLICY_BLOCK_PATTERNS.items():
        if reason_code in approved_reasons:
            continue
        if any(pattern.lower() in joined for pattern in patterns):
            return reason_code
    return None


def _incident_risk_level(task: dict[str, Any]) -> str:
    incident = task.get("incident") or {}
    raw = str(incident.get("severity") or IncidentSeverity.MEDIUM.value).strip().lower()
    if raw not in {IncidentSeverity.LOW.value, IncidentSeverity.MEDIUM.value, IncidentSeverity.HIGH.value, IncidentSeverity.CRITICAL.value}:
        return IncidentSeverity.MEDIUM.value
    return raw


def _incident_requires_approval(risk_level: str) -> bool:
    return risk_level in INCIDENT_RISK_APPROVAL_REQUIRED


def _incident_summary(task: dict[str, Any]) -> str:
    incident = task.get("incident") or {}
    return str(incident.get("summary") or "").strip()


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


def _build_incident_action_cards(task: dict[str, Any]) -> list[dict[str, Any]]:
    incident = task.get("incident") or {}
    context = task.get("incident_context") or {}
    risk_level = _incident_risk_level(task)
    evidence_links = _collect_incident_evidence(context)
    summary = _incident_summary(task)

    payload: dict[str, Any] = {
        "project_id": "OPS",
        "subject": f"[INCIDENT] {incident.get('service', 'unknown-service')} {incident.get('severity', 'unknown')}",
        "description": summary,
        "priority": "High" if risk_level in {IncidentSeverity.HIGH.value, IncidentSeverity.CRITICAL.value} else "Normal",
    }
    if str(incident.get("source") or "").strip().lower() == "simulate_mcp_timeout":
        payload["simulate_timeout"] = True

    return [
        {
            "action_id": f"act_{uuid4().hex[:12]}",
            "incident_id": incident.get("incident_id"),
            "title": "Create incident ticket and assign on-call",
            "action_type": "redmine_issue_create",
            "risk_level": risk_level,
            "approval_required": _incident_requires_approval(risk_level),
            "evidence_links": evidence_links,
            "mcp_call": {
                "method": "issue.create",
                "payload": payload,
            },
        }
    ]


def _evaluate_incident_action_gate(
    task: dict[str, Any],
    action_card: dict[str, Any],
    approved_reasons: set[str],
) -> tuple[str, str | None]:
    reason_code = _detect_policy_block(
        {
            "summary": _incident_summary(task),
            "method": action_card.get("mcp_call", {}).get("method"),
            "payload": action_card.get("mcp_call", {}).get("payload"),
        },
        approved_reasons,
    )
    if reason_code:
        return "BLOCKED_POLICY", reason_code

    if not action_card.get("evidence_links"):
        missing_reason = "missing_evidence"
        if missing_reason not in approved_reasons:
            return "NEEDS_APPROVAL", missing_reason

    if action_card.get("approval_required"):
        risk_reason = f"{action_card.get('risk_level', 'high')}_risk_action"
        if risk_reason not in approved_reasons:
            return "NEEDS_APPROVAL", risk_reason

    return "APPROVED", None


def _extract_points(notes: str, limit: int = 5) -> list[str]:
    raw_lines = notes.replace("\r", "\n").split("\n")
    lines = [line.strip("-* \t") for line in raw_lines if line.strip()]
    if not lines and notes.strip():
        return [notes.strip()]
    return lines[:limit]


def _render_meeting_summary(task: dict[str, Any]) -> str:
    payload = task["input"]
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


def _create_approval_item(task: dict[str, Any], reason_code: str) -> str:
    queue_id = f"aq_{uuid4().hex}"
    now = _now_iso()
    APPROVAL_QUEUE[queue_id] = {
        "queue_id": queue_id,
        "task_id": task["task_id"],
        "request_id": f"req_{uuid4().hex[:10]}",
        "reason_code": reason_code,
        "reason_message": f"approval required: {reason_code}",
        "requested_by": task["requested_by"],
        "approver_group": "ops_team",
        "status": ApprovalStatus.PENDING.value,
        "created_at": now,
        "expires_at": None,
        "resolved_at": None,
    }
    _persist_approval(APPROVAL_QUEUE[queue_id])
    _log_event(task["task_id"], "APPROVAL_REQUESTED", queue_id=queue_id, reason_code=reason_code)
    return queue_id


def _render_incident_report(task: dict[str, Any], action_results: list[dict[str, Any]]) -> str:
    incident = task.get("incident") or {}
    lines = [
        "# Incident Orchestration Report",
        "",
        f"- incident_id: {incident.get('incident_id', 'N/A')}",
        f"- service: {incident.get('service', 'N/A')}",
        f"- severity: {incident.get('severity', 'N/A')}",
        f"- policy_profile: {incident.get('policy_profile', 'N/A')}",
        f"- dry_run: {task.get('incident_runtime', {}).get('dry_run', True)}",
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
        task = TASKS[task_id]
        template_type = task["template_type"]
        if template_type != "meeting_summary":
            raise ValueError(f"unsupported template_type at runtime: {template_type}")
        report_text = _render_meeting_summary(task)

    report_path = _write_report(task_id, report_text)

    with STORE_LOCK:
        task = TASKS[task_id]
        _set_stage(task, "reviewer")
        if "# 회의 결과 요약" not in report_text:
            raise ValueError("review failed: report header missing")

        _set_stage(task, "reporter")
        task["result"] = {"report_path": report_path}
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

    dry_run = bool(runtime.get("dry_run", True))
    knowledge = INCIDENT_ADAPTERS["knowledge_rag"](
        query=f"{incident.get('service', 'unknown-service')} {incident.get('summary', '')}".strip(),
        team="platform",
        time_range="90d",
        dry_run=dry_run,
        timeout_seconds=3.0,
    )
    system = INCIDENT_ADAPTERS["system_rag"](
        incident_id=str(incident.get("incident_id") or ""),
        service=str(incident.get("service") or ""),
        window=str(incident.get("time_window") or "15m"),
        dry_run=dry_run,
        timeout_seconds=3.0,
    )
    context = {"knowledge": knowledge, "system": system}

    with STORE_LOCK:
        task = TASKS[task_id]
        task["incident_context"] = context
        task["updated_at"] = _now_iso()
        _persist_task(task)
        _log_event(
            task_id,
            "INCIDENT_CONTEXT_BUILT",
            evidence_count=len(knowledge.get("evidence", [])),
            signal_count=len(system.get("signals", [])),
        )
        _set_stage(task, "executor")
        action_cards = _build_incident_action_cards(task)
        task["action_cards"] = action_cards
        task["updated_at"] = _now_iso()
        _persist_task(task)
        _log_event(task_id, "INCIDENT_ACTIONS_PLANNED", count=len(action_cards))

        for action_card in action_cards:
            gate_result, reason_code = _evaluate_incident_action_gate(task, action_card, approved_reasons)
            if gate_result == "BLOCKED_POLICY":
                _log_event(task_id, "BLOCKED_POLICY", reason_code=reason_code, action_id=action_card.get("action_id"))
                queue_id = _create_approval_item(task, str(reason_code))
                _set_status(
                    task,
                    TaskStatus.NEEDS_HUMAN_APPROVAL,
                    reason_code=reason_code,
                    next_action="approve_or_reject",
                    approval_queue_id=queue_id,
                )
                return False
            if gate_result == "NEEDS_APPROVAL":
                queue_id = _create_approval_item(task, str(reason_code))
                _set_status(
                    task,
                    TaskStatus.NEEDS_HUMAN_APPROVAL,
                    reason_code=reason_code,
                    next_action="approve_or_reject",
                    approval_queue_id=queue_id,
                )
                _log_event(task_id, "INCIDENT_APPROVAL_QUEUED", action_id=action_card.get("action_id"), reason_code=reason_code)
                return False

        actor_context = {
            "actor_id": task.get("requested_by"),
            "actor_role": "requester",
        }

    action_results: list[dict[str, Any]] = []
    for action_card in action_cards:
        mcp_call = action_card.get("mcp_call", {})
        method = str(mcp_call.get("method") or "")
        payload = dict(mcp_call.get("payload") or {})
        if bool(payload.get("simulate_timeout")):
            raise TimeoutError("simulated incident mcp timeout")
        mcp_result = INCIDENT_ADAPTERS["redmine_mcp"](
            method=method,
            payload=payload,
            actor_context=actor_context,
            dry_run=dry_run,
            timeout_seconds=3.0,
        )
        action_results.append(
            {
                "action_id": action_card.get("action_id"),
                "status": "dry-run",
                "method": method,
                "external_ref": mcp_result.get("response", {}).get("external_ref"),
            }
        )
        _log_event(
            task_id,
            "INCIDENT_ACTION_EXECUTED",
            action_id=action_card.get("action_id"),
            method=method,
            mode=mcp_result.get("mode"),
            external_ref=mcp_result.get("response", {}).get("external_ref"),
        )

    with STORE_LOCK:
        task = TASKS[task_id]
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


@APP.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@APP.post("/api/v1/task/create", status_code=201)
def create_task(
    req: CreateTaskRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    role = _authorize(actor.actor_role, {"requester", "admin"}, "create_task")
    if role == "requester" and actor.actor_id != req.requested_by:
        _error(403, "FORBIDDEN", "requester must match requested_by")

    _validate_task_input(req.template_type, req.input)
    task_id = f"task_{uuid4()}"
    now = _now_iso()

    with STORE_LOCK:
        TASKS[task_id] = {
            "task_id": task_id,
            "workflow_type": TASK_WORKFLOW,
            "title": req.title,
            "template_type": req.template_type,
            "input": req.input,
            "requested_by": req.requested_by,
            "status": TaskStatus.READY.value,
            "current_stage": None,
            "next_action": "run_task",
            "retry_count": 0,
            "approved_reasons": [],
            "approval_queue_id": None,
            "approval_reason": None,
            "last_error": None,
            "result": None,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
            "final_reason": None,
        }
        _persist_task(TASKS[task_id])
        _log_event(task_id, "TASK_CREATED", actor_id=actor.actor_id, actor_role=role, requested_by=req.requested_by)

    return {"task_id": task_id, "status": TaskStatus.READY.value, "created_at": now}


@APP.post("/api/v1/task/run", status_code=202)
def run_task(
    req: RunTaskRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    with STORE_LOCK:
        task = TASKS.get(req.task_id)
        if not task:
            _error(404, "TASK_NOT_FOUND", f"task not found: {req.task_id}")
        _ensure_workflow(task, TASK_WORKFLOW, not_found_code="TASK_NOT_FOUND", not_found_message=f"task not found: {req.task_id}")
        role = _authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "admin"},
            action="run_task",
        )

        if req.idempotency_key:
            key = (req.task_id, req.idempotency_key)
            if key in RUN_IDEMPOTENCY:
                return {
                    "task_id": req.task_id,
                    "status": task["status"],
                    "started_at": task["started_at"],
                }

        if task["status"] != TaskStatus.READY.value:
            _error(409, "INVALID_TASK_STATE", f"task is not READY: {task['status']}")

        task["started_at"] = _now_iso()
        _set_status(task, TaskStatus.RUNNING, next_action="wait_for_completion")
        if req.idempotency_key:
            RUN_IDEMPOTENCY[(req.task_id, req.idempotency_key)] = req.task_id
            STATE_STORE.save_idempotency(req.task_id, req.idempotency_key, req.task_id)
        _log_event(task["task_id"], "RUN_REQUESTED", actor_id=actor.actor_id, actor_role=role)

    _start_pipeline(req.task_id)
    return {"task_id": req.task_id, "status": TaskStatus.RUNNING.value, "started_at": TASKS[req.task_id]["started_at"]}


@APP.get("/api/v1/task/status/{task_id}")
def task_status(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    with STORE_LOCK:
        task = TASKS.get(task_id)
        if not task:
            _error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
        _ensure_workflow(task, TASK_WORKFLOW, not_found_code="TASK_NOT_FOUND", not_found_message=f"task not found: {task_id}")
        _authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "reviewer", "approver", "admin"},
            action="task_status",
        )
        response: dict[str, Any] = {
            "task_id": task["task_id"],
            "status": task["status"],
            "current_stage": task["current_stage"],
            "last_event_at": task["updated_at"],
            "next_action": task.get("next_action"),
        }
        if task["status"] == TaskStatus.FAILED_RETRYABLE.value:
            response["retry_count"] = task["retry_count"]
            response["last_error"] = task["last_error"]
        if task["status"] == TaskStatus.NEEDS_HUMAN_APPROVAL.value:
            response["approval_reason"] = task.get("approval_reason")
            response["approval_queue_id"] = task.get("approval_queue_id")
            response["next_action"] = "approve_or_reject"
        if task["status"] == TaskStatus.DONE.value:
            if task.get("result"):
                response["result"] = task["result"]
            if task.get("completed_at"):
                response["completed_at"] = task["completed_at"]
            if task.get("final_reason"):
                response["final_reason"] = task["final_reason"]
        return response


@APP.get("/api/v1/task/events/{task_id}")
def task_events(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    with STORE_LOCK:
        task = TASKS.get(task_id)
        if not task:
            _error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
        _ensure_workflow(task, TASK_WORKFLOW, not_found_code="TASK_NOT_FOUND", not_found_message=f"task not found: {task_id}")
        _authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "reviewer", "approver", "admin"},
            action="task_events",
        )
        items = [event for event in TASK_EVENTS if event.get("task_id") == task_id]
        return {"task_id": task_id, "items": items, "count": len(items)}


@APP.post("/api/v1/incident/create", status_code=201)
def create_incident(
    req: CreateIncidentRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    role = _authorize(actor.actor_role, {"requester", "admin"}, "create_incident")
    if role == "requester" and actor.actor_id != req.requested_by:
        _error(403, "FORBIDDEN", "requester must match requested_by")

    task_id = f"incident_{uuid4()}"
    now = _now_iso()
    incident_payload = req.model_dump(mode="json")
    title = f"[incident] {req.service} {req.severity.value}"

    with STORE_LOCK:
        TASKS[task_id] = {
            "task_id": task_id,
            "workflow_type": INCIDENT_WORKFLOW,
            "title": title,
            "template_type": "incident_orchestration",
            "input": {"summary": req.summary, "service": req.service, "severity": req.severity.value},
            "incident": incident_payload,
            "incident_runtime": {"dry_run": bool(req.dry_run)},
            "requested_by": req.requested_by,
            "status": TaskStatus.READY.value,
            "current_stage": None,
            "next_action": "run_incident",
            "retry_count": 0,
            "approved_reasons": [],
            "approval_queue_id": None,
            "approval_reason": None,
            "last_error": None,
            "result": None,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
            "final_reason": None,
        }
        _persist_task(TASKS[task_id])
        _log_event(
            task_id,
            "INCIDENT_CREATED",
            actor_id=actor.actor_id,
            actor_role=role,
            requested_by=req.requested_by,
            incident_id=req.incident_id,
        )

    return {
        "task_id": task_id,
        "incident_id": req.incident_id,
        "status": TaskStatus.READY.value,
        "created_at": now,
    }


@APP.post("/api/v1/incident/run", status_code=202)
def run_incident(
    req: RunIncidentRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    with STORE_LOCK:
        task = TASKS.get(req.task_id)
        if not task:
            _error(404, "INCIDENT_NOT_FOUND", f"incident not found: {req.task_id}")
        _ensure_workflow(
            task,
            INCIDENT_WORKFLOW,
            not_found_code="INCIDENT_NOT_FOUND",
            not_found_message=f"incident not found: {req.task_id}",
        )
        role = _authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "admin"},
            action="run_incident",
        )

        if req.idempotency_key:
            key = (req.task_id, req.idempotency_key)
            if key in RUN_IDEMPOTENCY:
                return {
                    "task_id": req.task_id,
                    "status": task["status"],
                    "started_at": task["started_at"],
                }

        if task["status"] != TaskStatus.READY.value:
            _error(409, "INVALID_TASK_STATE", f"incident is not READY: {task['status']}")

        task["started_at"] = _now_iso()
        _set_status(task, TaskStatus.RUNNING, next_action="wait_for_completion")
        task.setdefault("incident_runtime", {})["dry_run"] = req.run_mode != "live"
        if req.idempotency_key:
            RUN_IDEMPOTENCY[(req.task_id, req.idempotency_key)] = req.task_id
            STATE_STORE.save_idempotency(req.task_id, req.idempotency_key, req.task_id)
        _log_event(task["task_id"], "INCIDENT_RUN_REQUESTED", actor_id=actor.actor_id, actor_role=role, run_mode=req.run_mode)

    _start_incident_pipeline(req.task_id)
    return {"task_id": req.task_id, "status": TaskStatus.RUNNING.value, "started_at": TASKS[req.task_id]["started_at"]}


@APP.get("/api/v1/incident/status/{task_id}")
def incident_status(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    with STORE_LOCK:
        task = TASKS.get(task_id)
        if not task:
            _error(404, "INCIDENT_NOT_FOUND", f"incident not found: {task_id}")
        _ensure_workflow(
            task,
            INCIDENT_WORKFLOW,
            not_found_code="INCIDENT_NOT_FOUND",
            not_found_message=f"incident not found: {task_id}",
        )
        _authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "reviewer", "approver", "admin"},
            action="incident_status",
        )
        response: dict[str, Any] = {
            "task_id": task["task_id"],
            "incident_id": task.get("incident", {}).get("incident_id"),
            "status": task["status"],
            "current_stage": task["current_stage"],
            "last_event_at": task["updated_at"],
            "next_action": task.get("next_action"),
        }
        if task["status"] == TaskStatus.FAILED_RETRYABLE.value:
            response["retry_count"] = task["retry_count"]
            response["last_error"] = task["last_error"]
        if task["status"] == TaskStatus.NEEDS_HUMAN_APPROVAL.value:
            response["approval_reason"] = task.get("approval_reason")
            response["approval_queue_id"] = task.get("approval_queue_id")
            response["next_action"] = "approve_or_reject"
        if task["status"] == TaskStatus.DONE.value:
            if task.get("result"):
                response["result"] = task["result"]
            if task.get("completed_at"):
                response["completed_at"] = task["completed_at"]
            if task.get("final_reason"):
                response["final_reason"] = task["final_reason"]
        return response


@APP.get("/api/v1/incident/events/{task_id}")
def incident_events(
    task_id: str,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    with STORE_LOCK:
        task = TASKS.get(task_id)
        if not task:
            _error(404, "INCIDENT_NOT_FOUND", f"incident not found: {task_id}")
        _ensure_workflow(
            task,
            INCIDENT_WORKFLOW,
            not_found_code="INCIDENT_NOT_FOUND",
            not_found_message=f"incident not found: {task_id}",
        )
        _authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "reviewer", "approver", "admin"},
            action="incident_events",
        )
        items = [event for event in TASK_EVENTS if event.get("task_id") == task_id]
        return {"task_id": task_id, "items": items, "count": len(items)}


@APP.get("/api/v1/approvals")
def list_approvals(
    status: str | None = Query(default=None),
    approver_group: str | None = Query(default=None),
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    _authorize(actor.actor_role, {"approver", "admin"}, "list_approvals")
    with STORE_LOCK:
        items = list(APPROVAL_QUEUE.values())
        if status:
            items = [item for item in items if item["status"] == status]
        if approver_group:
            items = [item for item in items if item["approver_group"] == approver_group]
        return {"items": items, "count": len(items)}


@APP.post("/api/v1/approvals/{queue_id}/approve")
def approve_queue_item(
    queue_id: str,
    req: ApprovalDecisionRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    role = _authorize(actor.actor_role, {"approver", "admin"}, "approve_queue_item")
    if req.acted_by != actor.actor_id:
        _error(403, "FORBIDDEN", "acted_by must match authenticated actor")
    with STORE_LOCK:
        queue_item = APPROVAL_QUEUE.get(queue_id)
        if not queue_item:
            _error(404, "APPROVAL_NOT_FOUND", f"approval queue item not found: {queue_id}")
        if queue_item["status"] != ApprovalStatus.PENDING.value:
            _error(409, "INVALID_APPROVAL_STATE", f"approval item is not PENDING: {queue_item['status']}")

        queue_item["status"] = ApprovalStatus.APPROVED.value
        queue_item["resolved_at"] = _now_iso()
        _persist_approval(queue_item)

        action = {
            "action_id": f"aa_{uuid4().hex}",
            "queue_id": queue_id,
            "task_id": queue_item["task_id"],
            "action": "APPROVE",
            "acted_by": actor.actor_id,
            "comment": req.comment,
            "created_at": _now_iso(),
        }
        APPROVAL_ACTIONS.append(action)
        _persist_approval_action(action)

        task = TASKS.get(queue_item["task_id"])
        if not task:
            _error(404, "TASK_NOT_FOUND", f"task not found: {queue_item['task_id']}")

        approved_reasons = set(task.get("approved_reasons", []))
        approved_reasons.add(queue_item["reason_code"])
        task["approved_reasons"] = sorted(approved_reasons)
        _set_status(task, TaskStatus.RUNNING, next_action="wait_for_completion")
        _log_event(task["task_id"], "HUMAN_APPROVED", queue_id=queue_id, acted_by=actor.actor_id, actor_role=role)

    _start_pipeline_for_workflow(task)
    return {"queue_id": queue_id, "status": ApprovalStatus.APPROVED.value, "task_status": TaskStatus.RUNNING.value}


@APP.post("/api/v1/approvals/{queue_id}/reject")
def reject_queue_item(
    queue_id: str,
    req: ApprovalDecisionRequest,
    actor: ActorContext = Depends(actor_context_dependency),
) -> dict[str, Any]:
    role = _authorize(actor.actor_role, {"approver", "admin"}, "reject_queue_item")
    if req.acted_by != actor.actor_id:
        _error(403, "FORBIDDEN", "acted_by must match authenticated actor")
    with STORE_LOCK:
        queue_item = APPROVAL_QUEUE.get(queue_id)
        if not queue_item:
            _error(404, "APPROVAL_NOT_FOUND", f"approval queue item not found: {queue_id}")
        if queue_item["status"] != ApprovalStatus.PENDING.value:
            _error(409, "INVALID_APPROVAL_STATE", f"approval item is not PENDING: {queue_item['status']}")

        queue_item["status"] = ApprovalStatus.REJECTED.value
        queue_item["resolved_at"] = _now_iso()
        _persist_approval(queue_item)

        action = {
            "action_id": f"aa_{uuid4().hex}",
            "queue_id": queue_id,
            "task_id": queue_item["task_id"],
            "action": "REJECT",
            "acted_by": actor.actor_id,
            "comment": req.comment,
            "created_at": _now_iso(),
        }
        APPROVAL_ACTIONS.append(action)
        _persist_approval_action(action)

        task = TASKS.get(queue_item["task_id"])
        if not task:
            _error(404, "TASK_NOT_FOUND", f"task not found: {queue_item['task_id']}")
        # Set completion timestamp before status persistence so DB state is consistent after restart.
        task["completed_at"] = _now_iso()
        _set_status(task, TaskStatus.DONE, next_action="none", final_reason="rejected_by_human")
        _log_event(task["task_id"], "HUMAN_REJECTED", queue_id=queue_id, acted_by=actor.actor_id, actor_role=role)

    return {"queue_id": queue_id, "status": ApprovalStatus.REJECTED.value, "task_status": TaskStatus.DONE.value}


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
