from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import uuid4

from app.auth import ActorContext


@dataclass
class ApprovalServiceDeps:
    store_lock: Any
    tasks: dict[str, dict[str, Any]]
    approval_queue: dict[str, dict[str, Any]]
    approval_actions: list[dict[str, Any]]
    approval_status_pending: str
    approval_status_approved: str
    approval_status_rejected: str
    task_status_running: Any
    task_status_done: Any
    now_iso: Callable[[], str]
    error: Callable[..., None]
    authorize: Callable[..., str]
    persist_approval: Callable[[dict[str, Any]], None]
    persist_approval_action: Callable[[dict[str, Any]], None]
    set_status: Callable[..., None]
    log_event: Callable[..., None]
    start_pipeline_for_workflow: Callable[[dict[str, Any]], None]


class ApprovalService:
    def __init__(self, deps: ApprovalServiceDeps) -> None:
        self.deps = deps

    def _field(self, req: Any, name: str, default: Any = None) -> Any:
        if isinstance(req, Mapping):
            return req.get(name, default)
        return getattr(req, name, default)

    def _string_value(self, value: Any) -> str:
        return str(getattr(value, "value", value))

    def _task_summary(self, task: dict[str, Any] | None) -> dict[str, Any] | None:
        if not task:
            return None
        return {
            "task_id": task.get("task_id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "requested_by": task.get("requested_by"),
            "updated_at": task.get("updated_at"),
            "approval_reason": task.get("approval_reason"),
        }

    def list_approvals(self, status: str | None, approver_group: str | None, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, {"approver", "admin"}, "list_approvals")
        with self.deps.store_lock:
            items = list(self.deps.approval_queue.values())
            if status:
                items = [item for item in items if item["status"] == status]
            if approver_group:
                items = [item for item in items if item["approver_group"] == approver_group]
            return {"items": items, "count": len(items)}

    def get_approval(self, queue_id: str, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, {"approver", "admin"}, "get_approval")
        with self.deps.store_lock:
            queue_item = self.deps.approval_queue.get(queue_id)
            if not queue_item:
                self.deps.error(404, "APPROVAL_NOT_FOUND", f"approval queue item not found: {queue_id}")
            actions = [item for item in self.deps.approval_actions if item.get("queue_id") == queue_id]
            actions.sort(key=lambda item: str(item.get("created_at") or ""))
            task = self.deps.tasks.get(queue_item["task_id"])
            return {
                "queue_id": queue_id,
                "item": dict(queue_item),
                "task_summary": self._task_summary(task),
                "actions": actions,
                "action_count": len(actions),
            }

    def approve(self, queue_id: str, req: Any, actor: ActorContext) -> dict[str, Any]:
        role = self.deps.authorize(actor.actor_role, {"approver", "admin"}, "approve_queue_item")
        acted_by = str(self._field(req, "acted_by", "") or "")
        if acted_by != actor.actor_id:
            self.deps.error(403, "FORBIDDEN", "acted_by must match authenticated actor")

        task: dict[str, Any] | None = None
        with self.deps.store_lock:
            queue_item = self.deps.approval_queue.get(queue_id)
            if not queue_item:
                self.deps.error(404, "APPROVAL_NOT_FOUND", f"approval queue item not found: {queue_id}")
            if queue_item["status"] != self.deps.approval_status_pending:
                self.deps.error(409, "INVALID_APPROVAL_STATE", f"approval item is not PENDING: {queue_item['status']}")

            queue_item["status"] = self.deps.approval_status_approved
            queue_item["resolved_at"] = self.deps.now_iso()
            self.deps.persist_approval(queue_item)

            action = {
                "action_id": f"aa_{uuid4().hex}",
                "queue_id": queue_id,
                "task_id": queue_item["task_id"],
                "action": "APPROVE",
                "acted_by": actor.actor_id,
                "comment": self._field(req, "comment"),
                "created_at": self.deps.now_iso(),
            }
            self.deps.approval_actions.append(action)
            self.deps.persist_approval_action(action)

            task = self.deps.tasks.get(queue_item["task_id"])
            if not task:
                self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {queue_item['task_id']}")

            approved_reasons = set(task.get("approved_reasons", []))
            approved_reasons.add(queue_item["reason_code"])
            task["approved_reasons"] = sorted(approved_reasons)
            self.deps.set_status(task, self.deps.task_status_running, next_action="wait_for_completion")
            self.deps.log_event(task["task_id"], "HUMAN_APPROVED", queue_id=queue_id, acted_by=actor.actor_id, actor_role=role)

        self.deps.start_pipeline_for_workflow(task)
        return {
            "queue_id": queue_id,
            "status": self.deps.approval_status_approved,
            "task_status": self._string_value(self.deps.task_status_running),
        }

    def reject(self, queue_id: str, req: Any, actor: ActorContext) -> dict[str, Any]:
        role = self.deps.authorize(actor.actor_role, {"approver", "admin"}, "reject_queue_item")
        acted_by = str(self._field(req, "acted_by", "") or "")
        if acted_by != actor.actor_id:
            self.deps.error(403, "FORBIDDEN", "acted_by must match authenticated actor")

        with self.deps.store_lock:
            queue_item = self.deps.approval_queue.get(queue_id)
            if not queue_item:
                self.deps.error(404, "APPROVAL_NOT_FOUND", f"approval queue item not found: {queue_id}")
            if queue_item["status"] != self.deps.approval_status_pending:
                self.deps.error(409, "INVALID_APPROVAL_STATE", f"approval item is not PENDING: {queue_item['status']}")

            queue_item["status"] = self.deps.approval_status_rejected
            queue_item["resolved_at"] = self.deps.now_iso()
            self.deps.persist_approval(queue_item)

            action = {
                "action_id": f"aa_{uuid4().hex}",
                "queue_id": queue_id,
                "task_id": queue_item["task_id"],
                "action": "REJECT",
                "acted_by": actor.actor_id,
                "comment": self._field(req, "comment"),
                "created_at": self.deps.now_iso(),
            }
            self.deps.approval_actions.append(action)
            self.deps.persist_approval_action(action)

            task = self.deps.tasks.get(queue_item["task_id"])
            if not task:
                self.deps.error(404, "TASK_NOT_FOUND", f"task not found: {queue_item['task_id']}")

            task["completed_at"] = self.deps.now_iso()
            self.deps.set_status(task, self.deps.task_status_done, next_action="none", final_reason="rejected_by_human")
            self.deps.log_event(task["task_id"], "HUMAN_REJECTED", queue_id=queue_id, acted_by=actor.actor_id, actor_role=role)

        return {
            "queue_id": queue_id,
            "status": self.deps.approval_status_rejected,
            "task_status": self._string_value(self.deps.task_status_done),
        }
