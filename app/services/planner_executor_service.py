from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping


ActionResult = dict[str, Any]
DispatchAction = Callable[..., ActionResult]
PersistTask = Callable[[dict[str, Any]], None]
NowIso = Callable[[], str]
LogEvent = Callable[..., None]
SetDoneStatus = Callable[[MutableMapping[str, Any]], None]


def build_action_result(
    planned_action: Mapping[str, Any],
    *,
    status: str,
    adapter: str,
    method: str,
    mode: str | None,
    request_payload: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> ActionResult:
    result: ActionResult = {
        "action_id": planned_action.get("action_id"),
        "status": status,
        "tool_id": planned_action.get("tool_id"),
        "adapter": adapter,
        "method": method,
        "mode": mode,
        "request_payload": dict(request_payload),
    }
    if extra:
        result.update(dict(extra))
    return result


def record_planning_snapshot(
    task: MutableMapping[str, Any],
    *,
    planned_actions: list[dict[str, Any]],
    planning_provenance: Mapping[str, Any],
    now_iso: NowIso,
    persist_task: PersistTask,
    extra_fields: Mapping[str, Any] | None = None,
) -> None:
    if extra_fields:
        for key, value in extra_fields.items():
            task[key] = value
    task["planned_actions"] = planned_actions
    task["planning_provenance"] = dict(planning_provenance)
    task["updated_at"] = now_iso()
    persist_task(dict(task))


def emit_planning_events(
    task_id: str,
    *,
    planning_provenance: Mapping[str, Any],
    planned_actions: list[dict[str, Any]],
    log_event: LogEvent,
    plan_generated_event: str,
    actions_planned_event: str,
    fallback_event: str | None = None,
) -> None:
    planner_selection = dict(planning_provenance.get("provider_selection") or {})
    if fallback_event and planning_provenance.get("fallback_reason"):
        log_event(
            task_id,
            fallback_event,
            source=planning_provenance.get("source"),
            fallback_reason=planning_provenance.get("fallback_reason"),
        )
    log_event(
        task_id,
        plan_generated_event,
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
    log_event(task_id, actions_planned_event, count=len(planned_actions))
    log_event(task_id, "PLANNED_ACTIONS_BUILT", count=len(planned_actions))


def execute_planned_actions(
    task: Mapping[str, Any],
    planned_actions: list[dict[str, Any]],
    *,
    dispatch_action: DispatchAction,
    dispatch_kwargs: Mapping[str, Any] | None = None,
) -> list[ActionResult]:
    action_results: list[ActionResult] = []
    base_kwargs = dict(dispatch_kwargs or {})
    for planned_action in planned_actions:
        action_results.append(
            dispatch_action(
                dict(task),
                planned_action,
                prior_results=action_results,
                **base_kwargs,
            )
        )
    return action_results


def record_action_results(
    task: MutableMapping[str, Any],
    *,
    action_results: list[ActionResult],
    now_iso: NowIso,
    persist_task: PersistTask,
    serializer: Callable[[ActionResult], ActionResult] | None = None,
    extra_fields: Mapping[str, Any] | None = None,
) -> None:
    normalize = serializer or (lambda item: dict(item))
    task["action_results"] = [normalize(item) for item in action_results]
    if extra_fields:
        for key, value in extra_fields.items():
            task[key] = value
    task["updated_at"] = now_iso()
    persist_task(dict(task))


def record_provider_selection(
    task: MutableMapping[str, Any],
    *,
    selection: Mapping[str, Any],
    now_iso: NowIso,
    persist_task: PersistTask,
    log_event: LogEvent,
) -> dict[str, Any]:
    normalized_selection = dict(selection)
    task["provider_selection"] = normalized_selection
    task["updated_at"] = now_iso()
    persist_task(dict(task))
    log_event(
        str(task.get("task_id") or ""),
        "MODEL_PROVIDER_SELECTED",
        provider_id=normalized_selection.get("provider_id"),
        provider_type=normalized_selection.get("provider_type"),
        engine=normalized_selection.get("engine"),
        model=normalized_selection.get("model"),
        selection_source=normalized_selection.get("selection_source"),
        sensitivity=normalized_selection.get("sensitivity"),
        task_type=normalized_selection.get("task_type"),
        external_send=normalized_selection.get("external_send"),
        requires_human_approval=normalized_selection.get("requires_human_approval"),
    )
    return normalized_selection


def write_report(
    reports_root: Path,
    task_id: str,
    report_text: str,
    *,
    filename: str = "report.md",
) -> str:
    target = reports_root / task_id
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / filename
    report_path.write_text(report_text, encoding="utf-8")
    return str(report_path)


def finalize_execution(
    task: MutableMapping[str, Any],
    *,
    result: Mapping[str, Any],
    now_iso: NowIso,
    set_done_status: SetDoneStatus,
) -> None:
    task["result"] = dict(result)
    task["completed_at"] = now_iso()
    set_done_status(task)
