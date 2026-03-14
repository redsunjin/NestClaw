from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException

from app.auth import ActorContext, VALID_ROLES
from app.main import build_approval_service, build_orchestration_service, build_tool_catalog_service, build_tool_draft_service


DEFAULT_ACTOR_ID = "user_cli"
DEFAULT_ACTOR_ROLE = "requester"
VALID_TASK_KINDS = ("auto", "task", "incident")
VALID_INCIDENT_RUN_MODES = ("dry-run", "mcp-live", "live")

CLI_ORCHESTRATION_SERVICE = build_orchestration_service(sync_execution=True)
CLI_APPROVAL_SERVICE = build_approval_service(sync_execution=True)
CLI_TOOL_CATALOG_SERVICE = build_tool_catalog_service()
CLI_TOOL_DRAFT_SERVICE = build_tool_draft_service()

MENU_ACTOR_ID = DEFAULT_ACTOR_ID
MENU_ACTOR_ROLE = DEFAULT_ACTOR_ROLE


def _error_payload(code: str, message: str, *, status_code: int = 1) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "status_code": status_code}}


def _coerce_http_error(exc: HTTPException) -> dict[str, Any]:
    if isinstance(exc.detail, dict):
        return exc.detail
    return _error_payload("HTTP_ERROR", str(exc.detail), status_code=exc.status_code)


def _actor_context(actor_id: str, actor_role: str, *, source: str = "cli") -> ActorContext:
    normalized_role = actor_role.strip().lower()
    if normalized_role not in VALID_ROLES:
        raise ValueError(f"unsupported actor_role: {actor_role}")
    return ActorContext(actor_id=actor_id.strip(), actor_role=normalized_role, source=source)


def _invoke(callable_obj: Any, *args: Any) -> tuple[dict[str, Any], int]:
    try:
        payload = callable_obj(*args)
    except HTTPException as exc:
        return _coerce_http_error(exc), 1
    except ValueError as exc:
        return _error_payload("INVALID_REQUEST", str(exc)), 1
    except Exception as exc:  # pragma: no cover - defensive
        return _error_payload("CLI_ERROR", str(exc)), 1
    return payload, 0


def _load_metadata(metadata_json: str | None, metadata_file: str | None) -> tuple[dict[str, Any], int]:
    if metadata_json and metadata_file:
        return _error_payload("INVALID_REQUEST", "use only one of --metadata-json or --metadata-file"), 1
    raw = metadata_json
    if metadata_file:
        try:
            raw = Path(metadata_file).read_text(encoding="utf-8")
        except FileNotFoundError:
            return _error_payload("INVALID_REQUEST", f"metadata file not found: {metadata_file}"), 1
    if not raw:
        return {}, 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return _error_payload("INVALID_REQUEST", f"invalid metadata json: {exc}"), 1
    if not isinstance(payload, dict):
        return _error_payload("INVALID_REQUEST", "metadata must be a JSON object"), 1
    return payload, 0


def _submit_payload(
    *,
    request_text: str,
    requested_by: str,
    task_kind: str = "auto",
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
    auto_run: bool = True,
    incident_run_mode: str = "dry-run",
    actor_id: str | None = None,
    actor_role: str = DEFAULT_ACTOR_ROLE,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id or requested_by, actor_role)
    payload = {
        "title": title,
        "task_kind": task_kind,
        "request_text": request_text,
        "metadata": dict(metadata or {}),
        "requested_by": requested_by,
        "auto_run": auto_run,
        "incident_run_mode": incident_run_mode,
    }
    return _invoke(CLI_ORCHESTRATION_SERVICE.submit_agent, payload, actor)


def _status_payload(task_id: str, *, actor_id: str, actor_role: str) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_ORCHESTRATION_SERVICE.agent_status, task_id, actor)


def _events_payload(task_id: str, *, actor_id: str, actor_role: str) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_ORCHESTRATION_SERVICE.agent_events, task_id, actor)


def _approve_payload(
    queue_id: str,
    *,
    acted_by: str,
    comment: str | None,
    actor_id: str | None = None,
    actor_role: str = "approver",
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id or acted_by, actor_role)
    return _invoke(CLI_APPROVAL_SERVICE.approve, queue_id, {"acted_by": acted_by, "comment": comment}, actor)


def _reject_payload(
    queue_id: str,
    *,
    acted_by: str,
    comment: str | None,
    actor_id: str | None = None,
    actor_role: str = "approver",
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id or acted_by, actor_role)
    return _invoke(CLI_APPROVAL_SERVICE.reject, queue_id, {"acted_by": acted_by, "comment": comment}, actor)


def _tools_payload(
    *,
    actor_id: str,
    actor_role: str,
    tool_id: str | None = None,
    capability_family: str | None = None,
    external_system: str | None = None,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    if tool_id:
        return _invoke(CLI_TOOL_CATALOG_SERVICE.get_tool, tool_id, actor)
    return _invoke(CLI_TOOL_CATALOG_SERVICE.list_tools, capability_family, external_system, actor)


def _tool_draft_payload(
    *,
    requested_by: str,
    request_text: str | None,
    actor_id: str,
    actor_role: str,
    tool_id: str | None = None,
    title: str | None = None,
    description: str | None = None,
    adapter: str | None = None,
    method: str | None = None,
    action_type: str | None = None,
    external_system: str | None = None,
    capability_family: str | None = None,
    required_payload_fields: list[str] | None = None,
    default_risk_level: str = "medium",
    default_approval_required: bool = True,
    supports_dry_run: bool = True,
    draft_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    if draft_id:
        return _invoke(CLI_TOOL_DRAFT_SERVICE.get_draft, draft_id, actor)
    payload = {
        "requested_by": requested_by,
        "request_text": request_text,
        "tool_id": tool_id,
        "title": title,
        "description": description,
        "adapter": adapter,
        "method": method,
        "action_type": action_type,
        "external_system": external_system,
        "capability_family": capability_family,
        "required_payload_fields": list(required_payload_fields or []),
        "default_risk_level": default_risk_level,
        "default_approval_required": default_approval_required,
        "supports_dry_run": supports_dry_run,
    }
    return _invoke(CLI_TOOL_DRAFT_SERVICE.create_draft, payload, actor)


def _tool_apply_payload(
    *,
    draft_id: str,
    acted_by: str,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    payload, exit_code = _invoke(CLI_TOOL_DRAFT_SERVICE.apply_draft, draft_id, {"acted_by": acted_by}, actor)
    if exit_code == 0:
        CLI_TOOL_CATALOG_SERVICE.deps.registry = build_tool_catalog_service().deps.registry
    return payload, exit_code


def _tool_validate_payload(
    *,
    draft_id: str,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_TOOL_DRAFT_SERVICE.validate_draft, draft_id, actor)


def _tool_rollback_payload(
    *,
    tool_id: str,
    acted_by: str,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    payload, exit_code = _invoke(CLI_TOOL_DRAFT_SERVICE.rollback_tool, tool_id, {"acted_by": acted_by}, actor)
    if exit_code == 0:
        CLI_TOOL_CATALOG_SERVICE.deps.registry = build_tool_catalog_service().deps.registry
    return payload, exit_code


def _print_status(payload: dict[str, Any]) -> None:
    print("\n[상태 보고]")
    print(f"- Task ID: {payload.get('task_id', '-')}")
    if payload.get("resolved_kind"):
        print(f"- 처리 종류: {payload.get('resolved_kind')}")
    print(f"- 현재 상태: {payload.get('status', '-')}")
    print(f"- 다음 액션: {payload.get('next_action', '-')}")
    if payload.get("status") == "NEEDS_HUMAN_APPROVAL":
        print(f"- 승인 필요 사유: {payload.get('approval_reason', '-')}")
        print(f"- 승인 큐 ID: {payload.get('approval_queue_id', '-')}")
    if payload.get("status") == "DONE":
        result = payload.get("result") or {}
        report_path = result.get("report_path")
        if report_path:
            print(f"- 결과 파일: {report_path}")
    if "error" in payload:
        err = payload["error"]
        print(f"- 오류: {err.get('code')}: {err.get('message')}")
    print()


def _print_events(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[이벤트]")
    for item in payload.get("items", [])[-10:]:
        print(f"- {item.get('created_at', '-')}: {item.get('event_type', '-')}")
    print()


def _print_approval_result(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[승인 처리]")
    print(f"- Queue ID: {payload.get('queue_id', '-')}")
    print(f"- 승인 상태: {payload.get('status', '-')}")
    print(f"- Task 상태: {payload.get('task_status', '-')}")
    print()


def _print_tools(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    if "items" in payload:
        print("\n[도구 목록]")
        for item in payload.get("items", []):
            print(f"- {item.get('tool_id')}: {item.get('title')} ({item.get('external_system')}/{item.get('capability_family')})")
        print()
        return
    print("\n[도구 상세]")
    print(f"- Tool ID: {payload.get('tool_id', '-')}")
    print(f"- 제목: {payload.get('title', '-')}")
    print(f"- 외부 시스템: {payload.get('external_system', '-')}")
    print(f"- 분류: {payload.get('capability_family', '-')}")
    print(f"- 메서드: {payload.get('method', '-')}")
    print(f"- Dry-run 지원: {payload.get('supports_dry_run', '-')}")
    print()


def _print_tool_draft(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[도구 등록 초안]")
    print(f"- Draft ID: {payload.get('draft_id', '-')}")
    print(f"- 파일: {payload.get('path', '-')}")
    tool = payload.get("tool") or {}
    if tool:
        print(f"- Tool ID: {tool.get('tool_id', '-')}")
        print(f"- Adapter: {tool.get('adapter', '-')}")
        print(f"- Method: {tool.get('method', '-')}")
    validation = payload.get("validation") or {}
    if validation:
        print(f"- Validation: {'PASS' if validation.get('valid') else 'FAIL'}")
    print()


def _emit_payload(payload: dict[str, Any], *, as_json: bool, command: str) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return
    if command == "tools":
        _print_tools(payload)
        return
    if command == "tool-draft":
        _print_tool_draft(payload)
        return
    if command == "tool-apply":
        _print_tool_draft(payload)
        return
    if command == "tool-validate":
        _print_tool_draft(payload)
        return
    if command == "tool-rollback":
        _print_tool_draft(payload)
        return
    if command == "events":
        _print_events(payload)
        return
    if command in {"approve", "reject"}:
        _print_approval_result(payload)
        return
    _print_status(payload)


def _input_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("필수 입력입니다.")


def _menu_submit() -> None:
    global MENU_ACTOR_ID, MENU_ACTOR_ROLE
    print("\n[Agent Submit]")
    task_kind = input("요청 유형 (auto/task/incident, 기본: auto): ").strip().lower() or "auto"
    title = input("작업 제목 (선택): ").strip() or None
    request_text = _input_required("요청 내용")
    requested_by = _input_required("요청자 ID")
    metadata: dict[str, Any] = {}
    run_mode = "dry-run"

    if task_kind in {"task", "meeting", "meeting_summary"}:
        metadata["meeting_title"] = input("회의 제목 (선택): ").strip() or title or "Agent Request"
        metadata["meeting_date"] = input("회의 날짜 (YYYY-MM-DD, 기본: 오늘): ").strip()
        participants_raw = input("참석자 (쉼표 구분, 기본: 요청자): ").strip()
        metadata["participants"] = [item.strip() for item in participants_raw.split(",") if item.strip()] if participants_raw else [requested_by]
        metadata["notes"] = input("회의 메모 (비우면 요청 내용 사용): ").strip() or request_text
        task_kind = "task"
    elif task_kind == "incident":
        metadata["service"] = _input_required("서비스명")
        metadata["severity"] = input("심각도 (low/medium/high/critical, 기본: low): ").strip().lower() or "low"
        metadata["source"] = input("감지 출처 (기본: agent): ").strip() or "agent"
        metadata["time_window"] = input("시간 구간 (기본: 15m): ").strip() or "15m"
        metadata["policy_profile"] = input("정책 프로필 (기본: default): ").strip() or "default"
        run_mode = input("incident run_mode (dry-run/mcp-live/live, 기본: dry-run): ").strip().lower() or "dry-run"

    MENU_ACTOR_ID = requested_by
    MENU_ACTOR_ROLE = "requester"
    payload, _ = _submit_payload(
        request_text=request_text,
        requested_by=requested_by,
        task_kind=task_kind,
        title=title,
        metadata=metadata,
        auto_run=True,
        incident_run_mode=run_mode,
        actor_id=MENU_ACTOR_ID,
        actor_role=MENU_ACTOR_ROLE,
    )
    _print_status(payload)


def _menu_status() -> None:
    payload, _ = _status_payload(_input_required("조회할 Task ID"), actor_id=MENU_ACTOR_ID, actor_role=MENU_ACTOR_ROLE)
    _print_status(payload)


def _menu_events() -> None:
    payload, _ = _events_payload(_input_required("이벤트 조회할 Task ID"), actor_id=MENU_ACTOR_ID, actor_role=MENU_ACTOR_ROLE)
    _print_events(payload)


def _menu_result() -> None:
    payload, _ = _status_payload(_input_required("결과 확인할 Task ID"), actor_id=MENU_ACTOR_ID, actor_role=MENU_ACTOR_ROLE)
    _print_status(payload)
    if payload.get("status") != "DONE":
        return
    report_path = ((payload.get("result") or {}).get("report_path"))
    if not report_path:
        return
    path = Path(str(report_path))
    if not path.exists():
        print("결과 파일이 아직 로컬에 없습니다.\n")
        return
    print("[결과 미리보기]")
    for line in path.read_text(encoding="utf-8").splitlines()[:20]:
        print(line)
    print()


def run_menu(*, actor_id: str = DEFAULT_ACTOR_ID, actor_role: str = DEFAULT_ACTOR_ROLE) -> int:
    global MENU_ACTOR_ID, MENU_ACTOR_ROLE
    MENU_ACTOR_ID = actor_id
    MENU_ACTOR_ROLE = actor_role

    menu = {
        "1": ("Agent 요청 제출", _menu_submit),
        "2": ("상태 조회", _menu_status),
        "3": ("이벤트 조회", _menu_events),
        "4": ("결과 확인", _menu_result),
        "5": ("종료", None),
    }

    print("NewClaw Agent CLI")
    print("- Mode: local sync service\n")
    print(f"- Actor ID: {MENU_ACTOR_ID}")
    print(f"- Actor Role: {MENU_ACTOR_ROLE}\n")

    while True:
        print("메뉴:")
        for key, (label, _) in menu.items():
            print(f"{key}. {label}")
        choice = input("선택: ").strip()
        if choice == "5":
            print("종료합니다.")
            return 0
        action = menu.get(choice, (None, None))[1]
        if action is None:
            print("올바른 번호를 선택하세요.\n")
            continue
        action()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="newclaw", description="NewClaw local tool CLI")
    subparsers = parser.add_subparsers(dest="command")

    menu_parser = subparsers.add_parser("menu", help="run interactive menu mode")
    menu_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    menu_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)

    submit_parser = subparsers.add_parser("submit", help="submit an agent request")
    submit_parser.add_argument("--request-text", required=True)
    submit_parser.add_argument("--requested-by", required=True)
    submit_parser.add_argument("--task-kind", choices=VALID_TASK_KINDS, default="auto")
    submit_parser.add_argument("--title")
    metadata_group = submit_parser.add_mutually_exclusive_group()
    metadata_group.add_argument("--metadata-json")
    metadata_group.add_argument("--metadata-file")
    submit_parser.add_argument("--actor-id")
    submit_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    submit_parser.add_argument("--incident-run-mode", choices=VALID_INCIDENT_RUN_MODES, default="dry-run")
    submit_parser.add_argument("--no-auto-run", action="store_true")
    submit_parser.add_argument("--json", action="store_true")

    status_parser = subparsers.add_parser("status", help="show agent status")
    status_parser.add_argument("--task-id", required=True)
    status_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    status_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    status_parser.add_argument("--json", action="store_true")

    events_parser = subparsers.add_parser("events", help="show agent events")
    events_parser.add_argument("--task-id", required=True)
    events_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    events_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    events_parser.add_argument("--json", action="store_true")

    approve_parser = subparsers.add_parser("approve", help="approve a pending queue item")
    approve_parser.add_argument("--queue-id", required=True)
    approve_parser.add_argument("--acted-by", required=True)
    approve_parser.add_argument("--comment")
    approve_parser.add_argument("--actor-id")
    approve_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default="approver")
    approve_parser.add_argument("--json", action="store_true")

    reject_parser = subparsers.add_parser("reject", help="reject a pending queue item")
    reject_parser.add_argument("--queue-id", required=True)
    reject_parser.add_argument("--acted-by", required=True)
    reject_parser.add_argument("--comment")
    reject_parser.add_argument("--actor-id")
    reject_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default="approver")
    reject_parser.add_argument("--json", action="store_true")

    tools_parser = subparsers.add_parser("tools", help="list or inspect registered execution tools")
    tools_parser.add_argument("--tool-id")
    tools_parser.add_argument("--capability-family")
    tools_parser.add_argument("--external-system")
    tools_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    tools_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    tools_parser.add_argument("--json", action="store_true")

    tool_draft_parser = subparsers.add_parser("tool-draft", help="create or fetch a tool registration draft")
    tool_draft_parser.add_argument("--draft-id")
    tool_draft_parser.add_argument("--requested-by", default=DEFAULT_ACTOR_ID)
    tool_draft_parser.add_argument("--request-text")
    tool_draft_parser.add_argument("--tool-id")
    tool_draft_parser.add_argument("--title")
    tool_draft_parser.add_argument("--description")
    tool_draft_parser.add_argument("--adapter")
    tool_draft_parser.add_argument("--method")
    tool_draft_parser.add_argument("--action-type")
    tool_draft_parser.add_argument("--external-system")
    tool_draft_parser.add_argument("--capability-family")
    tool_draft_parser.add_argument("--required-field", action="append", dest="required_fields", default=[])
    tool_draft_parser.add_argument("--default-risk-level", default="medium")
    tool_draft_parser.add_argument("--default-approval-required", action=argparse.BooleanOptionalAction, default=None)
    tool_draft_parser.add_argument("--supports-dry-run", action=argparse.BooleanOptionalAction, default=None)
    tool_draft_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    tool_draft_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    tool_draft_parser.add_argument("--json", action="store_true")

    tool_apply_parser = subparsers.add_parser("tool-apply", help="apply an approved tool registration draft")
    tool_apply_parser.add_argument("--draft-id", required=True)
    tool_apply_parser.add_argument("--acted-by", required=True)
    tool_apply_parser.add_argument("--actor-id")
    tool_apply_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default="approver")
    tool_apply_parser.add_argument("--json", action="store_true")

    tool_validate_parser = subparsers.add_parser("tool-validate", help="validate a tool registration draft")
    tool_validate_parser.add_argument("--draft-id", required=True)
    tool_validate_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    tool_validate_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    tool_validate_parser.add_argument("--json", action="store_true")

    tool_rollback_parser = subparsers.add_parser("tool-rollback", help="rollback the latest applied overlay change for a tool")
    tool_rollback_parser.add_argument("--tool-id", required=True)
    tool_rollback_parser.add_argument("--acted-by", required=True)
    tool_rollback_parser.add_argument("--actor-id")
    tool_rollback_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default="approver")
    tool_rollback_parser.add_argument("--json", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(argv) if argv is not None else sys.argv[1:]
    if not args_list:
        return run_menu()

    parser = build_parser()
    args = parser.parse_args(args_list)

    if args.command == "menu":
        return run_menu(actor_id=args.actor_id, actor_role=args.actor_role)

    if args.command == "submit":
        metadata, metadata_rc = _load_metadata(args.metadata_json, args.metadata_file)
        if metadata_rc != 0:
            _emit_payload(metadata, as_json=args.json, command="submit")
            return metadata_rc
        payload, exit_code = _submit_payload(
            request_text=args.request_text,
            requested_by=args.requested_by,
            task_kind=args.task_kind,
            title=args.title,
            metadata=metadata,
            auto_run=not args.no_auto_run,
            incident_run_mode=args.incident_run_mode,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="submit")
        return exit_code

    if args.command == "status":
        payload, exit_code = _status_payload(args.task_id, actor_id=args.actor_id, actor_role=args.actor_role)
        _emit_payload(payload, as_json=args.json, command="status")
        return exit_code

    if args.command == "events":
        payload, exit_code = _events_payload(args.task_id, actor_id=args.actor_id, actor_role=args.actor_role)
        _emit_payload(payload, as_json=args.json, command="events")
        return exit_code

    if args.command == "approve":
        payload, exit_code = _approve_payload(
            args.queue_id,
            acted_by=args.acted_by,
            comment=args.comment,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="approve")
        return exit_code

    if args.command == "reject":
        payload, exit_code = _reject_payload(
            args.queue_id,
            acted_by=args.acted_by,
            comment=args.comment,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="reject")
        return exit_code

    if args.command == "tools":
        payload, exit_code = _tools_payload(
            actor_id=args.actor_id,
            actor_role=args.actor_role,
            tool_id=args.tool_id,
            capability_family=args.capability_family,
            external_system=args.external_system,
        )
        _emit_payload(payload, as_json=args.json, command="tools")
        return exit_code

    if args.command == "tool-draft":
        payload, exit_code = _tool_draft_payload(
            requested_by=args.requested_by,
            request_text=args.request_text,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
            tool_id=args.tool_id,
            title=args.title,
            description=args.description,
            adapter=args.adapter,
            method=args.method,
            action_type=args.action_type,
            external_system=args.external_system,
            capability_family=args.capability_family,
            required_payload_fields=args.required_fields,
            default_risk_level=args.default_risk_level,
            default_approval_required=args.default_approval_required,
            supports_dry_run=args.supports_dry_run,
            draft_id=args.draft_id,
        )
        _emit_payload(payload, as_json=args.json, command="tool-draft")
        return exit_code

    if args.command == "tool-apply":
        payload, exit_code = _tool_apply_payload(
            draft_id=args.draft_id,
            acted_by=args.acted_by,
            actor_id=args.actor_id or args.acted_by,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="tool-apply")
        return exit_code

    if args.command == "tool-validate":
        payload, exit_code = _tool_validate_payload(
            draft_id=args.draft_id,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="tool-validate")
        return exit_code

    if args.command == "tool-rollback":
        payload, exit_code = _tool_rollback_payload(
            tool_id=args.tool_id,
            acted_by=args.acted_by,
            actor_id=args.actor_id or args.acted_by,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="tool-rollback")
        return exit_code

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
