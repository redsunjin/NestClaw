from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from app.auth import ActorContext
from app.runtime_taxonomy import runtime_state_summary


AGENT_TASK_KIND_AUTO = "auto"
AGENT_TASK_KIND_TASK = "task"
AGENT_TASK_KIND_INCIDENT = "incident"
AGENT_TASK_KINDS = {AGENT_TASK_KIND_AUTO, AGENT_TASK_KIND_TASK, AGENT_TASK_KIND_INCIDENT}
AGENT_INCIDENT_HINTS = {
    "incident",
    "outage",
    "sev1",
    "sev2",
    "sev-1",
    "sev-2",
    "degraded",
    "downtime",
    "latency",
    "on-call",
    "rollback",
    "alarm",
    "장애",
    "알람",
    "장애대응",
}


@dataclass
class OrchestrationServiceDeps:
    store_lock: Any
    tasks: dict[str, dict[str, Any]]
    task_events: list[dict[str, Any]]
    approval_queue: dict[str, dict[str, Any]]
    approval_actions: list[dict[str, Any]]
    run_idempotency: dict[tuple[str, str], str]
    state_store: Any
    reports_root: Any
    task_workflow: str
    incident_workflow: str
    agent_entrypoint: str
    task_status_ready: Any
    task_status_running: Any
    task_status_failed_retryable: Any
    task_status_needs_human_approval: Any
    task_status_done: Any
    now_iso: Callable[[], str]
    error: Callable[..., None]
    authorize: Callable[..., str]
    authorize_task_access: Callable[..., str]
    ensure_workflow: Callable[..., None]
    validate_task_input: Callable[[str, dict[str, Any]], None]
    set_status: Callable[..., None]
    workflow_type: Callable[[dict[str, Any]], str]
    apply_incident_run_mode: Callable[[dict[str, Any], str | None], dict[str, Any]]
    incident_runtime_snapshot: Callable[[dict[str, Any]], dict[str, Any]]
    normalize_incident_run_mode: Callable[[str | None], str]
    classify_agent_intent: Callable[[str, dict[str, Any]], dict[str, Any]]
    start_pipeline: Callable[[str], None]
    start_incident_pipeline: Callable[[str], None]
    persist_task: Callable[[dict[str, Any]], None]
    log_event: Callable[..., None]
    get_capability_manifest: Callable[[ActorContext], dict[str, Any]]


class OrchestrationService:
    def __init__(self, deps: OrchestrationServiceDeps) -> None:
        self.deps = deps

    def _field(self, req: Any, name: str, default: Any = None) -> Any:
        if isinstance(req, Mapping):
            return req.get(name, default)
        return getattr(req, name, default)

    def _request_mapping(self, req: Any) -> dict[str, Any]:
        if isinstance(req, Mapping):
            return dict(req)
        model_dump = getattr(req, "model_dump", None)
        if callable(model_dump):
            try:
                return dict(model_dump(mode="json"))
            except TypeError:
                return dict(model_dump())
        raw = getattr(req, "__dict__", None)
        if isinstance(raw, dict):
            return {key: value for key, value in raw.items() if not str(key).startswith("_")}
        return {}

    def _string_value(self, value: Any) -> str:
        return str(getattr(value, "value", value))

    def _status_value(self, value: Any) -> str:
        return self._string_value(value)

    def _today_iso(self) -> str:
        return self.deps.now_iso().split("T", 1)[0]

    def _normalize_agent_task_kind(self, raw_kind: str | None) -> str:
        kind = str(raw_kind or AGENT_TASK_KIND_AUTO).strip().lower()
        if kind in {"meeting", "meeting_summary"}:
            return AGENT_TASK_KIND_TASK
        if kind not in AGENT_TASK_KINDS:
            self.deps.error(400, "INVALID_REQUEST", f"unsupported task_kind: {raw_kind}")
        return kind

    def _infer_incident_severity(self, request_text: str, metadata: Mapping[str, Any]) -> str:
        raw = str(metadata.get("severity") or "").strip().lower()
        if raw in {"low", "medium", "high", "critical"}:
            return raw

        haystack = f"{request_text} {self._flatten_agent_text(dict(metadata))}".lower()
        if any(token in haystack for token in ("critical", "sev0", "sev-0", "sev1", "sev-1", "전면장애")):
            return "critical"
        if any(token in haystack for token in ("high", "major", "customer-facing", "customer facing", "outage", "장애")):
            return "high"
        if any(token in haystack for token in ("medium", "degraded", "latency", "warning", "slow")):
            return "medium"
        return "low"

    def _flatten_agent_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, Mapping):
            return " ".join(self._flatten_agent_text(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(self._flatten_agent_text(item) for item in value)
        return str(value).strip()

    def _requested_kind_classification(self, kind: str) -> dict[str, Any]:
        resolved_kind = AGENT_TASK_KIND_INCIDENT if kind == AGENT_TASK_KIND_INCIDENT else AGENT_TASK_KIND_TASK
        return {
            "resolved_kind": resolved_kind,
            "source": "requested_kind",
            "confidence": 1.0,
            "rationale": f"explicit task_kind={kind}",
            "provider_selection": None,
            "fallback_reason": None,
        }

    def detect_agent_workflow(self, req: Any) -> tuple[str, dict[str, Any]]:
        kind = self._normalize_agent_task_kind(self._field(req, "task_kind"))
        if kind == AGENT_TASK_KIND_INCIDENT:
            return self.deps.incident_workflow, self._requested_kind_classification(kind)
        if kind == AGENT_TASK_KIND_TASK:
            return self.deps.task_workflow, self._requested_kind_classification(kind)

        request_text = str(self._field(req, "request_text", "") or "")
        metadata = dict(self._field(req, "metadata", {}) or {})
        classification = dict(self.deps.classify_agent_intent(request_text, metadata))
        resolved_kind = str(classification.get("resolved_kind") or AGENT_TASK_KIND_TASK).strip().lower()
        if resolved_kind not in {AGENT_TASK_KIND_TASK, AGENT_TASK_KIND_INCIDENT}:
            self.deps.error(500, "INTENT_CLASSIFIER_ERROR", f"unsupported resolved_kind: {resolved_kind}")
        workflow = self.deps.incident_workflow if resolved_kind == AGENT_TASK_KIND_INCIDENT else self.deps.task_workflow
        return workflow, classification

    def _coerce_participants(self, value: Any, requested_by: str) -> list[str]:
        items: list[str] = []
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
        if not items:
            items = [requested_by]
        return items

    def build_agent_task_request(self, req: Any) -> dict[str, Any]:
        metadata = dict(self._field(req, "metadata", {}) or {})
        requested_by = str(self._field(req, "requested_by", "") or "")
        request_text = str(self._field(req, "request_text", "") or "")
        title = self._field(req, "title")
        meeting_title = str(metadata.get("meeting_title") or title or "Agent Request").strip()
        meeting_date = str(metadata.get("meeting_date") or self._today_iso()).strip() or self._today_iso()
        notes = str(metadata.get("notes") or request_text).strip() or request_text
        template_type = str(metadata.get("template_type") or "meeting_summary").strip() or "meeting_summary"

        return {
            "title": str(title or meeting_title or "회의요약 생성").strip() or "회의요약 생성",
            "template_type": template_type,
            "input": {
                "meeting_title": meeting_title or "Agent Request",
                "meeting_date": meeting_date,
                "participants": self._coerce_participants(metadata.get("participants"), requested_by),
                "notes": notes,
            },
            "requested_by": requested_by,
        }

    def build_agent_incident_request(self, req: Any) -> dict[str, Any]:
        metadata = dict(self._field(req, "metadata", {}) or {})
        request_text = str(self._field(req, "request_text", "") or "")
        run_mode = self.deps.normalize_incident_run_mode(self._field(req, "incident_run_mode"))
        summary = str(metadata.get("summary") or request_text).strip() or request_text
        service = str(metadata.get("service") or metadata.get("component") or "unknown-service").strip() or "unknown-service"
        source = str(metadata.get("source") or "agent").strip() or "agent"
        time_window = str(metadata.get("time_window") or "15m").strip() or "15m"
        policy_profile = str(metadata.get("policy_profile") or "default").strip() or "default"
        incident_id = str(metadata.get("incident_id") or f"inc-{uuid4().hex[:8]}").strip() or f"inc-{uuid4().hex[:8]}"
        notify_channel = str(metadata.get("notify_channel") or "").strip() or None

        return {
            "incident_id": incident_id,
            "service": service,
            "severity": self._infer_incident_severity(request_text, metadata),
            "detected_at": str(metadata.get("detected_at") or self.deps.now_iso()).strip() or self.deps.now_iso(),
            "source": source,
            "summary": summary,
            "time_window": time_window,
            "requested_by": str(self._field(req, "requested_by", "") or ""),
            "policy_profile": policy_profile,
            "dry_run": run_mode != "live",
            "notify_channel": notify_channel,
        }

    def _resolved_kind_from_workflow(self, workflow: str) -> str:
        if workflow == self.deps.incident_workflow:
            return AGENT_TASK_KIND_INCIDENT
        return AGENT_TASK_KIND_TASK

    def _resolved_kind_for_task(self, task: dict[str, Any]) -> str:
        return self._resolved_kind_from_workflow(self.deps.workflow_type(task))

    def annotate_agent_task(self, task_id: str, req: Any, workflow: str, classification: Mapping[str, Any]) -> None:
        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                return
            task["entrypoint"] = self.deps.agent_entrypoint
            task["agent_request"] = {
                "request_text": self._field(req, "request_text"),
                "task_kind": self._normalize_agent_task_kind(self._field(req, "task_kind")),
                "title": self._field(req, "title"),
                "metadata": dict(self._field(req, "metadata", {}) or {}),
            }
            task["agent_route"] = self._resolved_kind_from_workflow(workflow)
            task["intent_classification"] = dict(classification)
            task["updated_at"] = self.deps.now_iso()
            self.deps.persist_task(task)
            provider_selection = dict((classification.get("provider_selection") or {}))
            self.deps.log_event(
                task_id,
                "INTENT_CLASSIFIED",
                resolved_kind=task["agent_route"],
                source=classification.get("source"),
                confidence=classification.get("confidence"),
                provider_id=provider_selection.get("provider_id"),
            )
            self.deps.log_event(
                task_id,
                "AGENT_ROUTED",
                resolved_kind=task["agent_route"],
                requested_kind=task["agent_request"]["task_kind"],
                classification_source=classification.get("source"),
            )

    def build_task_status_payload(self, task: dict[str, Any]) -> dict[str, Any]:
        response: dict[str, Any] = {
            "task_id": task["task_id"],
            "status": task["status"],
            "current_stage": task["current_stage"],
            "last_event_at": task["updated_at"],
            "next_action": task.get("next_action"),
            "state_summary": runtime_state_summary(
                task,
                ready_status=self._status_value(self.deps.task_status_ready),
                running_status=self._status_value(self.deps.task_status_running),
                failed_retryable_status=self._status_value(self.deps.task_status_failed_retryable),
                needs_human_approval_status=self._status_value(self.deps.task_status_needs_human_approval),
                done_status=self._status_value(self.deps.task_status_done),
            ),
        }
        if task.get("provider_selection"):
            response["provider_selection"] = task["provider_selection"]
        if task.get("planning_provenance"):
            response["planning_provenance"] = task["planning_provenance"]
        if task.get("provider_invocation"):
            response["provider_invocation"] = task["provider_invocation"]
        if task.get("planned_actions"):
            response["planned_actions"] = task["planned_actions"]
        if task.get("action_results"):
            response["action_results"] = task["action_results"]
        if task.get("action_cards"):
            response["action_cards"] = task["action_cards"]
        if task["status"] == self._status_value(self.deps.task_status_failed_retryable):
            response["retry_count"] = task["retry_count"]
            response["last_error"] = task["last_error"]
        if task["status"] == self._status_value(self.deps.task_status_needs_human_approval):
            response["approval_reason"] = task.get("approval_reason")
            response["approval_queue_id"] = task.get("approval_queue_id")
            response["next_action"] = "approve_or_reject"
        if task["status"] == self._status_value(self.deps.task_status_done):
            if task.get("result"):
                response["result"] = task["result"]
            if task.get("completed_at"):
                response["completed_at"] = task["completed_at"]
            if task.get("final_reason"):
                response["final_reason"] = task["final_reason"]
        return response

    def build_incident_status_payload(self, task: dict[str, Any]) -> dict[str, Any]:
        response = self.build_task_status_payload(task)
        response["incident_id"] = task.get("incident", {}).get("incident_id")
        response["run_mode"] = self.deps.incident_runtime_snapshot(dict(task.get("incident_runtime") or {}))["run_mode"]
        return response

    def build_events_payload(self, task_id: str) -> dict[str, Any]:
        items = [event for event in self.deps.task_events if event.get("task_id") == task_id]
        return {"task_id": task_id, "items": items, "count": len(items)}

    def build_agent_status_payload(self, task: dict[str, Any]) -> dict[str, Any]:
        if self.deps.workflow_type(task) == self.deps.incident_workflow:
            response = self.build_incident_status_payload(task)
        else:
            response = self.build_task_status_payload(task)
        response["entrypoint"] = self.deps.agent_entrypoint
        response["resolved_kind"] = str(task.get("agent_route") or self._resolved_kind_for_task(task))
        response["title"] = task.get("title")
        response["requested_by"] = task.get("requested_by")
        if task.get("intent_classification"):
            response["intent_classification"] = task["intent_classification"]
        request_text = str((task.get("agent_request") or {}).get("request_text") or task.get("title") or "").strip()
        if request_text:
            response["request_summary"] = request_text[:240]
        return response

    def build_agent_events_payload(self, task: dict[str, Any]) -> dict[str, Any]:
        response = self.build_events_payload(task["task_id"])
        response["entrypoint"] = self.deps.agent_entrypoint
        response["resolved_kind"] = str(task.get("agent_route") or self._resolved_kind_for_task(task))
        return response

    def _get_agent_task(self, task_id: str, actor: ActorContext, *, action: str) -> dict[str, Any]:
        task = self.deps.tasks.get(task_id)
        if not task:
            self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
        self.deps.authorize_task_access(
            task,
            actor.actor_id,
            actor.actor_role,
            allowed_roles={"requester", "reviewer", "approver", "admin"},
            action=action,
        )
        return task

    def _reports_root_path(self) -> Path:
        root = Path(self.deps.reports_root)
        if not root.is_absolute():
            root = (Path.cwd() / root).resolve()
        return root.resolve()

    def _task_summary(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "task_id": task.get("task_id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "requested_by": task.get("requested_by"),
            "updated_at": task.get("updated_at"),
            "approval_reason": task.get("approval_reason"),
            "state_summary": runtime_state_summary(
                task,
                ready_status=self._status_value(self.deps.task_status_ready),
                running_status=self._status_value(self.deps.task_status_running),
                failed_retryable_status=self._status_value(self.deps.task_status_failed_retryable),
                needs_human_approval_status=self._status_value(self.deps.task_status_needs_human_approval),
                done_status=self._status_value(self.deps.task_status_done),
            ),
        }

    def _resolve_report_path(self, task: dict[str, Any]) -> Path:
        report_path_value = str((task.get("result") or {}).get("report_path") or "").strip()
        if not report_path_value:
            self.deps.error(404, "REPORT_NOT_FOUND", f"report not found for task: {task['task_id']}")

        report_path = Path(report_path_value)
        if not report_path.is_absolute():
            report_path = (Path.cwd() / report_path).resolve()
        else:
            report_path = report_path.resolve()

        try:
            report_path.relative_to(self._reports_root_path())
        except ValueError:
            self.deps.error(500, "REPORT_PATH_INVALID", f"report path escaped reports root: {task['task_id']}")

        if not report_path.is_file():
            self.deps.error(404, "REPORT_NOT_FOUND", f"report file not found: {task['task_id']}")
        return report_path

    def _agent_recent_item(self, task: dict[str, Any]) -> dict[str, Any]:
        result = task.get("result") or {}
        planning = task.get("planning_provenance") or {}
        provider_selection = planning.get("provider_selection") or {}
        planned_actions = list(task.get("planned_actions") or [])
        action_results = list(task.get("action_results") or [])
        state_summary = runtime_state_summary(
            task,
            ready_status=self._status_value(self.deps.task_status_ready),
            running_status=self._status_value(self.deps.task_status_running),
            failed_retryable_status=self._status_value(self.deps.task_status_failed_retryable),
            needs_human_approval_status=self._status_value(self.deps.task_status_needs_human_approval),
            done_status=self._status_value(self.deps.task_status_done),
        )
        return {
            "task_id": task["task_id"],
            "title": task.get("title"),
            "requested_by": task.get("requested_by"),
            "status": task.get("status"),
            "resolved_kind": str(task.get("agent_route") or self._resolved_kind_for_task(task)),
            "entrypoint": task.get("entrypoint") or self.deps.agent_entrypoint,
            "updated_at": task.get("updated_at"),
            "created_at": task.get("created_at"),
            "current_stage": task.get("current_stage"),
            "next_action": task.get("next_action"),
            "approval_queue_id": task.get("approval_queue_id"),
            "report_path": result.get("report_path"),
            "actions_executed": result.get("actions_executed"),
            "planning_source": planning.get("source"),
            "planning_provider_id": provider_selection.get("provider_id"),
            "planning_rationale": planning.get("rationale"),
            "planning_confidence": planning.get("confidence"),
            "planning_degraded_mode": planning.get("degraded_mode"),
            "planning_fallback_reason": planning.get("fallback_reason"),
            "planned_tool_ids": [str(item.get("tool_id") or "") for item in planned_actions if item.get("tool_id")],
            "executed_tool_ids": [str(item.get("tool_id") or "") for item in action_results if item.get("tool_id")],
            "run_mode": self.deps.incident_runtime_snapshot(dict(task.get("incident_runtime") or {}))["run_mode"]
            if self.deps.workflow_type(task) == self.deps.incident_workflow
            else None,
            "state_summary": state_summary,
        }

    def _stage12_job_metadata(self, task: dict[str, Any]) -> dict[str, Any]:
        metadata = dict((task.get("agent_request") or {}).get("metadata") or {})
        stage12_job = dict(metadata.get("stage12_job") or {})
        template_id = str(stage12_job.get("template_id") or "").strip()
        if not template_id:
            return {}
        return stage12_job

    def _job_run_history_item(self, task: dict[str, Any]) -> dict[str, Any]:
        result = dict(task.get("result") or {})
        planning = dict(task.get("planning_provenance") or {})
        provider_selection = dict(planning.get("provider_selection") or {})
        planned_actions = list(task.get("planned_actions") or [])
        action_results = list(task.get("action_results") or [])
        stage12_job = self._stage12_job_metadata(task)
        state_summary = runtime_state_summary(
            task,
            ready_status=self._status_value(self.deps.task_status_ready),
            running_status=self._status_value(self.deps.task_status_running),
            failed_retryable_status=self._status_value(self.deps.task_status_failed_retryable),
            needs_human_approval_status=self._status_value(self.deps.task_status_needs_human_approval),
            done_status=self._status_value(self.deps.task_status_done),
        )
        return {
            "run_id": task["task_id"],
            "task_id": task["task_id"],
            "template_id": stage12_job.get("template_id"),
            "profile_id": stage12_job.get("profile_id"),
            "provider_id": stage12_job.get("provider_id"),
            "provider_class": stage12_job.get("provider_class"),
            "capability_pack_ids": list(stage12_job.get("capability_pack_ids") or []),
            "budget_enforcement": dict(stage12_job.get("budget_enforcement") or {}),
            "status": task.get("status"),
            "resolved_kind": str(task.get("agent_route") or self._resolved_kind_for_task(task)),
            "title": task.get("title"),
            "requested_by": task.get("requested_by"),
            "created_at": task.get("created_at"),
            "started_at": task.get("started_at"),
            "completed_at": task.get("completed_at"),
            "updated_at": task.get("updated_at"),
            "current_stage": task.get("current_stage"),
            "next_action": task.get("next_action"),
            "approval_queue_id": task.get("approval_queue_id"),
            "approval_reason": task.get("approval_reason"),
            "report_path": result.get("report_path"),
            "actions_executed": result.get("actions_executed"),
            "run_mode": self.deps.incident_runtime_snapshot(dict(task.get("incident_runtime") or {}))["run_mode"]
            if self.deps.workflow_type(task) == self.deps.incident_workflow
            else None,
            "planning_source": planning.get("source"),
            "planning_provider_id": provider_selection.get("provider_id"),
            "planning_rationale": planning.get("rationale"),
            "planning_confidence": planning.get("confidence"),
            "planning_degraded_mode": planning.get("degraded_mode"),
            "planning_fallback_reason": planning.get("fallback_reason"),
            "planned_tool_ids": [str(item.get("tool_id") or "") for item in planned_actions if item.get("tool_id")],
            "executed_tool_ids": [str(item.get("tool_id") or "") for item in action_results if item.get("tool_id")],
            "state_summary": state_summary,
        }

    def _report_preview_from_path(self, task: dict[str, Any], report_path: Path | None, *, max_chars: int) -> dict[str, Any]:
        if report_path is None:
            return {
                "available": False,
                "task_id": task["task_id"],
                "resolved_kind": str(task.get("agent_route") or self._resolved_kind_for_task(task)),
                "status": task.get("status"),
                "report_path": None,
                "report_name": None,
                "preview_text": "",
                "preview_chars": max_chars,
                "truncated": False,
                "raw_url": None,
                "reason": "report_not_ready",
            }

        report_text = report_path.read_text(encoding="utf-8")
        preview_text = report_text[:max_chars]
        return {
            "available": True,
            "task_id": task["task_id"],
            "resolved_kind": str(task.get("agent_route") or self._resolved_kind_for_task(task)),
            "status": task.get("status"),
            "report_path": str(report_path.relative_to(Path.cwd())),
            "report_name": report_path.name,
            "preview_text": preview_text,
            "preview_chars": max_chars,
            "truncated": len(report_text) > max_chars,
            "raw_url": f"/api/v1/agent/report/{task['task_id']}/raw",
        }

    def _approval_bundle_payload(self, task: dict[str, Any], actor: ActorContext) -> dict[str, Any]:
        queue_id = str(task.get("approval_queue_id") or "").strip()
        if not queue_id:
            return {
                "available": False,
                "queue_id": None,
                "access_level": "none",
                "approval_reason": task.get("approval_reason"),
                "item": None,
                "task_summary": self._task_summary(task),
                "actions": [],
                "action_count": 0,
            }

        queue_item = self.deps.approval_queue.get(queue_id)
        actions = [item for item in self.deps.approval_actions if item.get("queue_id") == queue_id]
        actions.sort(key=lambda item: str(item.get("created_at") or ""))
        summary_item = dict(queue_item) if queue_item else {"queue_id": queue_id, "task_id": task.get("task_id")}

        payload = {
            "available": True,
            "queue_id": queue_id,
            "access_level": "summary",
            "approval_reason": task.get("approval_reason"),
            "item": summary_item,
            "task_summary": self._task_summary(task),
            "actions": [],
            "action_count": len(actions),
        }
        if actor.actor_role in {"approver", "admin"}:
            payload["access_level"] = "detail"
            payload["actions"] = actions
        return payload

    def create_task(self, req: Any, actor: ActorContext) -> dict[str, Any]:
        role = self.deps.authorize(actor.actor_role, {"requester", "admin"}, "create_task")
        requested_by = str(self._field(req, "requested_by", "") or "")
        if role == "requester" and actor.actor_id != requested_by:
            self.deps.error(403, "FORBIDDEN", "requester must match requested_by")

        template_type = str(self._field(req, "template_type", "") or "")
        task_input = dict(self._field(req, "input", {}) or {})
        self.deps.validate_task_input(template_type, task_input)
        task_id = f"task_{uuid4()}"
        now = self.deps.now_iso()

        with self.deps.store_lock:
            self.deps.tasks[task_id] = {
                "task_id": task_id,
                "workflow_type": self.deps.task_workflow,
                "title": str(self._field(req, "title", "") or ""),
                "template_type": template_type,
                "input": task_input,
                "requested_by": requested_by,
                "status": self._status_value(self.deps.task_status_ready),
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
            self.deps.persist_task(self.deps.tasks[task_id])
            self.deps.log_event(task_id, "TASK_CREATED", actor_id=actor.actor_id, actor_role=role, requested_by=requested_by)

        return {"task_id": task_id, "status": self._status_value(self.deps.task_status_ready), "created_at": now}

    def run_task(self, req: Any, actor: ActorContext) -> dict[str, Any]:
        task_id = str(self._field(req, "task_id", "") or "")
        started_at = None

        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
            self.deps.ensure_workflow(
                task,
                self.deps.task_workflow,
                not_found_code="TASK_NOT_FOUND",
                not_found_message=f"task not found: {task_id}",
            )
            role = self.deps.authorize_task_access(
                task,
                actor.actor_id,
                actor.actor_role,
                allowed_roles={"requester", "admin"},
                action="run_task",
            )

            idempotency_key = self._field(req, "idempotency_key")
            if idempotency_key:
                key = (task_id, str(idempotency_key))
                if key in self.deps.run_idempotency:
                    return {
                        "task_id": task_id,
                        "status": task["status"],
                        "started_at": task["started_at"],
                    }

            if task["status"] != self._status_value(self.deps.task_status_ready):
                self.deps.error(409, "INVALID_TASK_STATE", f"task is not READY: {task['status']}")

            task["started_at"] = self.deps.now_iso()
            started_at = task["started_at"]
            self.deps.set_status(task, self.deps.task_status_running, next_action="wait_for_completion")
            if idempotency_key:
                key = (task_id, str(idempotency_key))
                self.deps.run_idempotency[key] = task_id
                self.deps.state_store.save_idempotency(task_id, str(idempotency_key), task_id)
            self.deps.log_event(task["task_id"], "RUN_REQUESTED", actor_id=actor.actor_id, actor_role=role)

        self.deps.start_pipeline(task_id)
        return {"task_id": task_id, "status": self._status_value(self.deps.task_status_running), "started_at": started_at}

    def task_status(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
            self.deps.ensure_workflow(
                task,
                self.deps.task_workflow,
                not_found_code="TASK_NOT_FOUND",
                not_found_message=f"task not found: {task_id}",
            )
            self.deps.authorize_task_access(
                task,
                actor.actor_id,
                actor.actor_role,
                allowed_roles={"requester", "reviewer", "approver", "admin"},
                action="task_status",
            )
            return self.build_task_status_payload(task)

    def task_events(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
            self.deps.ensure_workflow(
                task,
                self.deps.task_workflow,
                not_found_code="TASK_NOT_FOUND",
                not_found_message=f"task not found: {task_id}",
            )
            self.deps.authorize_task_access(
                task,
                actor.actor_id,
                actor.actor_role,
                allowed_roles={"requester", "reviewer", "approver", "admin"},
                action="task_events",
            )
            return self.build_events_payload(task_id)

    def create_incident(self, req: Any, actor: ActorContext) -> dict[str, Any]:
        role = self.deps.authorize(actor.actor_role, {"requester", "admin"}, "create_incident")
        requested_by = str(self._field(req, "requested_by", "") or "")
        if role == "requester" and actor.actor_id != requested_by:
            self.deps.error(403, "FORBIDDEN", "requester must match requested_by")

        task_id = f"incident_{uuid4()}"
        now = self.deps.now_iso()
        incident_payload = self._request_mapping(req)
        service_name = str(self._field(req, "service", "") or "")
        severity = self._string_value(self._field(req, "severity", ""))
        title = f"[incident] {service_name} {severity}"

        with self.deps.store_lock:
            incident_runtime = self.deps.apply_incident_run_mode(
                {},
                "dry-run" if bool(self._field(req, "dry_run", True)) else "live",
            )
            self.deps.tasks[task_id] = {
                "task_id": task_id,
                "workflow_type": self.deps.incident_workflow,
                "title": title,
                "template_type": "incident_orchestration",
                "input": {
                    "summary": str(self._field(req, "summary", "") or ""),
                    "service": service_name,
                    "severity": severity,
                },
                "incident": incident_payload,
                "incident_runtime": incident_runtime,
                "requested_by": requested_by,
                "status": self._status_value(self.deps.task_status_ready),
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
            self.deps.persist_task(self.deps.tasks[task_id])
            self.deps.log_event(
                task_id,
                "INCIDENT_CREATED",
                actor_id=actor.actor_id,
                actor_role=role,
                requested_by=requested_by,
                incident_id=str(self._field(req, "incident_id", "") or ""),
            )

        return {
            "task_id": task_id,
            "incident_id": str(self._field(req, "incident_id", "") or ""),
            "status": self._status_value(self.deps.task_status_ready),
            "created_at": now,
        }

    def run_incident(self, req: Any, actor: ActorContext) -> dict[str, Any]:
        task_id = str(self._field(req, "task_id", "") or "")
        started_at = None

        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "INCIDENT_NOT_FOUND", f"incident not found: {task_id}")
            self.deps.ensure_workflow(
                task,
                self.deps.incident_workflow,
                not_found_code="INCIDENT_NOT_FOUND",
                not_found_message=f"incident not found: {task_id}",
            )
            role = self.deps.authorize_task_access(
                task,
                actor.actor_id,
                actor.actor_role,
                allowed_roles={"requester", "admin"},
                action="run_incident",
            )

            idempotency_key = self._field(req, "idempotency_key")
            if idempotency_key:
                key = (task_id, str(idempotency_key))
                if key in self.deps.run_idempotency:
                    return {
                        "task_id": task_id,
                        "status": task["status"],
                        "started_at": task["started_at"],
                    }

            if task["status"] != self._status_value(self.deps.task_status_ready):
                self.deps.error(409, "INVALID_TASK_STATE", f"incident is not READY: {task['status']}")

            task["started_at"] = self.deps.now_iso()
            started_at = task["started_at"]
            self.deps.set_status(task, self.deps.task_status_running, next_action="wait_for_completion")
            runtime = dict(task.get("incident_runtime") or {})
            task["incident_runtime"] = self.deps.apply_incident_run_mode(runtime, self._field(req, "run_mode"))
            if idempotency_key:
                key = (task_id, str(idempotency_key))
                self.deps.run_idempotency[key] = task_id
                self.deps.state_store.save_idempotency(task_id, str(idempotency_key), task_id)
            self.deps.log_event(
                task["task_id"],
                "INCIDENT_RUN_REQUESTED",
                actor_id=actor.actor_id,
                actor_role=role,
                run_mode=task["incident_runtime"]["run_mode"],
            )

        self.deps.start_incident_pipeline(task_id)
        return {"task_id": task_id, "status": self._status_value(self.deps.task_status_running), "started_at": started_at}

    def incident_status(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "INCIDENT_NOT_FOUND", f"incident not found: {task_id}")
            self.deps.ensure_workflow(
                task,
                self.deps.incident_workflow,
                not_found_code="INCIDENT_NOT_FOUND",
                not_found_message=f"incident not found: {task_id}",
            )
            self.deps.authorize_task_access(
                task,
                actor.actor_id,
                actor.actor_role,
                allowed_roles={"requester", "reviewer", "approver", "admin"},
                action="incident_status",
            )
            return self.build_incident_status_payload(task)

    def incident_events(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "INCIDENT_NOT_FOUND", f"incident not found: {task_id}")
            self.deps.ensure_workflow(
                task,
                self.deps.incident_workflow,
                not_found_code="INCIDENT_NOT_FOUND",
                not_found_message=f"incident not found: {task_id}",
            )
            self.deps.authorize_task_access(
                task,
                actor.actor_id,
                actor.actor_role,
                allowed_roles={"requester", "reviewer", "approver", "admin"},
                action="incident_events",
            )
            return self.build_events_payload(task_id)

    def submit_agent(self, req: Any, actor: ActorContext) -> dict[str, Any]:
        workflow, classification = self.detect_agent_workflow(req)
        auto_run = bool(self._field(req, "auto_run", True))
        idempotency_key = self._field(req, "idempotency_key")

        if workflow == self.deps.incident_workflow:
            created = self.create_incident(self.build_agent_incident_request(req), actor)
            task_id = str(created["task_id"])
            self.annotate_agent_task(task_id, req, workflow, classification)
            if auto_run:
                self.run_incident(
                    {
                        "task_id": task_id,
                        "idempotency_key": idempotency_key,
                        "run_mode": self._field(req, "incident_run_mode", "dry-run"),
                    },
                    actor,
                )
        else:
            created = self.create_task(self.build_agent_task_request(req), actor)
            task_id = str(created["task_id"])
            self.annotate_agent_task(task_id, req, workflow, classification)
            if auto_run:
                self.run_task(
                    {
                        "task_id": task_id,
                        "idempotency_key": idempotency_key,
                        "run_mode": "standard",
                    },
                    actor,
                )

        with self.deps.store_lock:
            task = self.deps.tasks.get(task_id)
            if not task:
                self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {task_id}")
            response = self.build_agent_status_payload(task)
            response["created_at"] = task["created_at"]
            response["started_at"] = task.get("started_at")
            response["auto_run"] = auto_run
            return response

    def agent_status(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        with self.deps.store_lock:
            task = self._get_agent_task(task_id, actor, action="agent_status")
            return self.build_agent_status_payload(task)

    def agent_events(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        with self.deps.store_lock:
            task = self._get_agent_task(task_id, actor, action="agent_events")
            return self.build_agent_events_payload(task)

    def agent_report(self, task_id: str, actor: ActorContext, *, max_chars: int = 4000) -> dict[str, Any]:
        normalized_max_chars = max(200, min(int(max_chars or 4000), 20000))
        with self.deps.store_lock:
            task = self._get_agent_task(task_id, actor, action="agent_report")
            report_path = self._resolve_report_path(task)
        return self._report_preview_from_path(task, report_path, max_chars=normalized_max_chars)

    def agent_report_path(self, task_id: str, actor: ActorContext) -> Path:
        with self.deps.store_lock:
            task = self._get_agent_task(task_id, actor, action="agent_report_raw")
            return self._resolve_report_path(task)

    def agent_bundle(self, task_id: str, actor: ActorContext, *, max_chars: int = 4000) -> dict[str, Any]:
        normalized_max_chars = max(200, min(int(max_chars or 4000), 20000))
        with self.deps.store_lock:
            task = self._get_agent_task(task_id, actor, action="agent_bundle")
            status_payload = self.build_agent_status_payload(task)
            events_payload = self.build_agent_events_payload(task)
            approval_payload = self._approval_bundle_payload(task, actor)
            report_path: Path | None = None
            if str((task.get("result") or {}).get("report_path") or "").strip():
                report_path = self._resolve_report_path(task)

        report_payload = self._report_preview_from_path(task, report_path, max_chars=normalized_max_chars)
        capability_snapshot = self.deps.get_capability_manifest(actor)
        return {
            "bundle_version": "v1",
            "task_id": task["task_id"],
            "resolved_kind": status_payload.get("resolved_kind"),
            "generated_at": self.deps.now_iso(),
            "status": status_payload,
            "events": events_payload,
            "report": report_payload,
            "approval": approval_payload,
            "capabilities": {
                "source": "capabilities",
                "snapshot": capability_snapshot,
            },
        }

    def _handoff_packet_type(self, status_payload: Mapping[str, Any], approval_payload: Mapping[str, Any]) -> str:
        state_summary = dict(status_payload.get("state_summary") or {})
        canonical_state = str(state_summary.get("canonical_state") or "")
        canonical_reason = str(state_summary.get("canonical_reason_code") or "")
        if canonical_state == "done":
            return "completed"
        if canonical_state == "approval_pending" or bool(approval_payload.get("available")):
            return "approval_pending"
        if canonical_state in {"retryable_failure", "blocked"} or canonical_reason in {"retryable_failure", "env_blocked"}:
            return "blocked"
        return "observe"

    def _handoff_owner(self, packet_type: str) -> str:
        if packet_type == "approval_pending":
            return "approver_admin"
        if packet_type == "blocked":
            return "operator_or_integration_owner"
        if packet_type == "completed":
            return "requester_or_operator"
        return "requester_or_reviewer"

    def _handoff_actions(
        self,
        packet_type: str,
        status_payload: Mapping[str, Any],
        approval_payload: Mapping[str, Any],
        report_payload: Mapping[str, Any],
    ) -> list[str]:
        queue_id = str(approval_payload.get("queue_id") or "").strip()
        if packet_type == "approval_pending":
            actions = []
            if queue_id:
                actions.append(f"Review approval queue item `{queue_id}` and confirm policy intent.")
            actions.append("Approver/admin should decide approve or reject before resuming execution.")
            actions.append("Re-open the handoff packet or bundle after the approval decision to confirm the next state.")
            return actions
        if packet_type == "completed":
            actions = ["Review report preview or raw report and hand the final output to the operator or requester."]
            if report_payload.get("available"):
                actions.append("Use the raw report path or URL as the canonical completion artifact.")
            actions.append("If operator acknowledgment is needed, attach this packet to the closeout thread.")
            return actions
        if packet_type == "blocked":
            return [
                "Inspect the canonical reason code, detail reason, and last error before retrying.",
                "Resolve the blocking runtime or external dependency condition, then re-run the workflow or readiness step.",
                "Escalate with this packet and the execution bundle if another owner must unblock the run.",
            ]
        return [
            "Keep observing status and events until the workflow reaches approval-pending, blocked, or completed state.",
            "Use the execution bundle for deeper planner/event detail if the operator needs a fuller audit trail.",
        ]

    def _handoff_markdown(self, packet: Mapping[str, Any]) -> str:
        summary = dict(packet.get("operator_summary") or {})
        planning = dict(packet.get("planning") or {})
        execution = dict(packet.get("execution") or {})
        approval = dict(packet.get("approval") or {})
        report = dict(packet.get("report") or {})
        readiness = dict(packet.get("environment_readiness") or {})
        actions = [str(item).strip() for item in packet.get("operator_actions") or [] if str(item).strip()]

        lines = [
            "# NestClaw Operator Handoff Packet",
            "",
            f"- packet_type: `{packet.get('packet_type', '-')}`",
            f"- task_id: `{packet.get('task_id', '-')}`",
            f"- resolved_kind: `{packet.get('resolved_kind', '-')}`",
            f"- recommended_handoff_owner: `{packet.get('recommended_handoff_owner', '-')}`",
            f"- current_status: `{summary.get('status', '-')}`",
            f"- canonical_state: `{summary.get('canonical_state', '-')}`",
            f"- canonical_reason_code: `{summary.get('canonical_reason_code', '-')}`",
            f"- title: `{summary.get('title', '-')}`",
            f"- requested_by: `{summary.get('requested_by', '-')}`",
            f"- next_action: `{summary.get('next_action', '-')}`",
            f"- current_stage: `{summary.get('current_stage', '-')}`",
            "",
            "## Planning",
            f"- source: `{planning.get('source', '-')}`",
            f"- provider_id: `{planning.get('provider_id', '-')}`",
            f"- degraded_mode: `{planning.get('degraded_mode', False)}`",
            f"- fallback_reason: `{planning.get('fallback_reason', '-')}`",
            f"- rationale: {planning.get('rationale', '-')}",
            "",
            "## Execution",
            f"- event_count: `{execution.get('event_count', 0)}`",
            f"- planned_tool_ids: `{', '.join(execution.get('planned_tool_ids') or []) or '-'}`",
            f"- executed_tool_ids: `{', '.join(execution.get('executed_tool_ids') or []) or '-'}`",
            f"- actions_executed: `{execution.get('actions_executed', '-')}`",
            "",
            "## Approval",
            f"- available: `{approval.get('available', False)}`",
            f"- queue_id: `{approval.get('queue_id', '-')}`",
            f"- access_level: `{approval.get('access_level', '-')}`",
            f"- approval_reason: `{approval.get('approval_reason', '-')}`",
            f"- item_status: `{approval.get('item_status', '-')}`",
            "",
            "## Report",
            f"- available: `{report.get('available', False)}`",
            f"- report_name: `{report.get('report_name', '-')}`",
            f"- raw_url: `{report.get('raw_url', '-')}`",
            f"- reason: `{report.get('reason', '-')}`",
            "",
            "## Environment Readiness",
            f"- stage8_live_status: `{readiness.get('status', '-')}`",
            f"- stage8_live_reason: `{readiness.get('canonical_reason_code', '-')}`",
            "",
            "## Recommended Operator Actions",
        ]
        for index, action in enumerate(actions, start=1):
            lines.append(f"{index}. {action}")
        preview_text = str(report.get("preview_text") or "").strip()
        if preview_text:
            lines.extend(["", "## Report Preview", preview_text])
        return "\n".join(lines).strip() + "\n"

    def agent_handoff(self, task_id: str, actor: ActorContext, *, max_chars: int = 1600) -> dict[str, Any]:
        normalized_max_chars = max(200, min(int(max_chars or 1600), 20000))
        bundle = self.agent_bundle(task_id, actor, max_chars=normalized_max_chars)
        status_payload = dict(bundle.get("status") or {})
        state_summary = dict(status_payload.get("state_summary") or {})
        approval_payload = dict(bundle.get("approval") or {})
        report_payload = dict(bundle.get("report") or {})
        capabilities = dict((bundle.get("capabilities") or {}).get("snapshot") or {})
        planning = dict(status_payload.get("planning_provenance") or {})
        provider_selection = dict(status_payload.get("provider_selection") or planning.get("provider_selection") or {})
        planned_actions = list(status_payload.get("planned_actions") or [])
        action_results = list(status_payload.get("action_results") or [])
        result = dict(status_payload.get("result") or {})
        packet_type = self._handoff_packet_type(status_payload, approval_payload)
        operator_actions = self._handoff_actions(packet_type, status_payload, approval_payload, report_payload)

        packet = {
            "packet_version": "v1",
            "source_bundle_version": bundle.get("bundle_version"),
            "packet_type": packet_type,
            "task_id": bundle.get("task_id"),
            "resolved_kind": bundle.get("resolved_kind"),
            "generated_at": self.deps.now_iso(),
            "recommended_handoff_owner": self._handoff_owner(packet_type),
            "operator_summary": {
                "title": status_payload.get("title"),
                "requested_by": status_payload.get("requested_by"),
                "status": status_payload.get("status"),
                "current_stage": status_payload.get("current_stage"),
                "next_action": status_payload.get("next_action"),
                "last_event_at": status_payload.get("last_event_at"),
                "request_summary": status_payload.get("request_summary"),
                "canonical_state": state_summary.get("canonical_state"),
                "canonical_reason_code": state_summary.get("canonical_reason_code"),
                "detail_reason_code": state_summary.get("detail_reason_code"),
                "state_message": state_summary.get("message"),
                "run_mode": status_payload.get("run_mode"),
            },
            "planning": {
                "source": planning.get("source"),
                "provider_id": provider_selection.get("provider_id"),
                "confidence": planning.get("confidence"),
                "rationale": planning.get("rationale"),
                "degraded_mode": bool(planning.get("degraded_mode")),
                "fallback_reason": planning.get("fallback_reason"),
            },
            "execution": {
                "event_count": int((bundle.get("events") or {}).get("count") or 0),
                "planned_action_count": len(planned_actions),
                "planned_tool_ids": [str(item.get("tool_id") or "") for item in planned_actions if item.get("tool_id")],
                "executed_action_count": len(action_results),
                "executed_tool_ids": [str(item.get("tool_id") or "") for item in action_results if item.get("tool_id")],
                "actions_executed": result.get("actions_executed"),
                "report_path": result.get("report_path"),
            },
            "approval": {
                "available": bool(approval_payload.get("available")),
                "queue_id": approval_payload.get("queue_id"),
                "access_level": approval_payload.get("access_level"),
                "approval_reason": approval_payload.get("approval_reason"),
                "item_status": ((approval_payload.get("item") or {}).get("status")),
                "approver_group": ((approval_payload.get("item") or {}).get("approver_group")),
                "action_count": approval_payload.get("action_count"),
                "actions": approval_payload.get("actions") or [],
            },
            "report": {
                "available": bool(report_payload.get("available")),
                "report_name": report_payload.get("report_name"),
                "report_path": report_payload.get("report_path"),
                "raw_url": report_payload.get("raw_url"),
                "reason": report_payload.get("reason"),
                "preview_text": report_payload.get("preview_text"),
                "truncated": report_payload.get("truncated"),
            },
            "environment_readiness": dict((capabilities.get("readiness") or {}).get("stage8_live_readiness") or {}),
            "operator_actions": operator_actions,
            "bundle_ref": {
                "http": f"/api/v1/agent/bundle/{task_id}",
                "cli": f"newclaw bundle --task-id {task_id} --actor-id <actor_id> --json",
                "mcp": "agent.bundle",
            },
        }
        packet["markdown"] = self._handoff_markdown(packet)
        return packet

    def agent_recent(self, actor: ActorContext, *, limit: int = 10) -> dict[str, Any]:
        normalized_limit = max(1, min(int(limit or 10), 50))
        with self.deps.store_lock:
            items = list(self.deps.tasks.values())
            if actor.actor_role == "requester":
                items = [item for item in items if item.get("requested_by") == actor.actor_id]
            else:
                self.deps.authorize(actor.actor_role, {"reviewer", "approver", "admin"}, "agent_recent")

            items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
            recent_items = [self._agent_recent_item(item) for item in items[:normalized_limit]]
            return {"items": recent_items, "count": len(recent_items), "limit": normalized_limit}

    def job_run_history(
        self,
        actor: ActorContext,
        *,
        limit: int = 10,
        template_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_limit = max(1, min(int(limit or 10), 50))
        template_filter = str(template_id or "").strip()
        with self.deps.store_lock:
            items = [item for item in self.deps.tasks.values() if self._stage12_job_metadata(item)]
            if actor.actor_role == "requester":
                items = [item for item in items if item.get("requested_by") == actor.actor_id]
            else:
                self.deps.authorize(actor.actor_role, {"reviewer", "approver", "admin"}, "job_run_history")
            if template_filter:
                items = [
                    item
                    for item in items
                    if str(self._stage12_job_metadata(item).get("template_id") or "") == template_filter
                ]
            items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
            history_items = [self._job_run_history_item(item) for item in items[:normalized_limit]]
            return {
                "surface": "job.history",
                "items": history_items,
                "count": len(history_items),
                "limit": normalized_limit,
                "template_filter": template_filter or None,
            }
