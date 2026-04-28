from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException

from app.auth import ActorContext, VALID_ROLES
from app.main import (
    build_approval_service,
    build_capability_manifest_service,
    build_orchestration_service,
    build_tool_catalog_service,
    build_tool_draft_service,
)
from app.stage12_jobs import (
    job_describe_payload as stage12_job_describe_payload,
    job_list_payload as stage12_job_list_payload,
    run_stage12_job,
)


DEFAULT_ACTOR_ID = "user_cli"
DEFAULT_ACTOR_ROLE = "requester"
VALID_TASK_KINDS = ("auto", "task", "incident")
VALID_INCIDENT_RUN_MODES = ("dry-run", "mcp-live", "live")
AGENT_PROFILES_PATH = Path("configs/agent_profiles.json")
JOB_TEMPLATES_PATH = Path("configs/job_templates.json")
CAPABILITY_PACKS_PATH = Path("configs/capability_packs.json")
IMPLEMENTED_JOB_TEMPLATE_IDS = {"daily_status_digest", "issue_triage", "readiness_check"}

CLI_ORCHESTRATION_SERVICE = build_orchestration_service(sync_execution=True)
CLI_APPROVAL_SERVICE = build_approval_service(sync_execution=True)
CLI_TOOL_CATALOG_SERVICE = build_tool_catalog_service()
CLI_CAPABILITY_MANIFEST_SERVICE = build_capability_manifest_service()
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


def _invoke(callable_obj: Any, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], int]:
    try:
        payload = callable_obj(*args, **kwargs)
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


def _load_json_document(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"registry file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json registry {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"registry must be a JSON object: {path}")
    return payload


def _registry_items_by_id(path: Path, collection_key: str, id_key: str) -> dict[str, dict[str, Any]]:
    document = _load_json_document(path)
    items = document.get(collection_key)
    if not isinstance(items, list):
        raise ValueError(f"registry {path} missing list: {collection_key}")
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in items:
        if not isinstance(raw_item, dict):
            raise ValueError(f"registry {path} contains non-object item")
        item_id = str(raw_item.get(id_key) or "").strip()
        if not item_id:
            raise ValueError(f"registry {path} item missing id field: {id_key}")
        if item_id in by_id:
            raise ValueError(f"registry {path} has duplicate id: {item_id}")
        by_id[item_id] = dict(raw_item)
    return by_id


def _load_stage12_job_registries() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    return (
        _registry_items_by_id(JOB_TEMPLATES_PATH, "templates", "template_id"),
        _registry_items_by_id(AGENT_PROFILES_PATH, "profiles", "profile_id"),
        _registry_items_by_id(CAPABILITY_PACKS_PATH, "packs", "pack_id"),
    )


def _job_input_payload(input_json: str | None, input_file: str | None) -> tuple[dict[str, Any], int]:
    if input_json and input_file:
        return _error_payload("INVALID_REQUEST", "use only one of --input-json or --input-file"), 1
    if not input_json and not input_file:
        return _error_payload("INVALID_REQUEST", "one of --input-json or --input-file is required"), 1
    raw = input_json
    if input_file:
        try:
            raw = Path(input_file).read_text(encoding="utf-8")
        except FileNotFoundError:
            return _error_payload("INVALID_REQUEST", f"input file not found: {input_file}"), 1
    try:
        payload = json.loads(str(raw or ""))
    except json.JSONDecodeError as exc:
        return _error_payload("INVALID_REQUEST", f"invalid input json: {exc}"), 1
    if not isinstance(payload, dict):
        return _error_payload("INVALID_REQUEST", "job input must be a JSON object"), 1
    return payload, 0


def _coerce_string_list(value: Any, *, fallback: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    elif value is None:
        items = []
    else:
        items = [str(value).strip()]
    return items or list(fallback or [])


def _source_line(source: Any) -> str:
    if isinstance(source, dict):
        name = str(source.get("name") or source.get("source") or source.get("id") or "source").strip()
        status = str(source.get("status") or "").strip()
        summary = str(source.get("summary") or source.get("note") or source.get("text") or "").strip()
        parts = [name]
        if status:
            parts.append(f"status={status}")
        if summary:
            parts.append(summary)
        return ": ".join([parts[0], " / ".join(parts[1:])]) if len(parts) > 1 else parts[0]
    return str(source).strip()


def _daily_status_notes(input_payload: dict[str, Any]) -> str:
    lines = [
        f"date: {input_payload.get('date')}",
        f"audience: {input_payload.get('audience')}",
        f"sensitivity: {input_payload.get('sensitivity')}",
        "sources:",
    ]
    sources = input_payload.get("sources")
    if isinstance(sources, list):
        source_lines = []
        for item in sources:
            line = _source_line(item)
            if line:
                source_lines.append(line)
    else:
        line = _source_line(sources)
        source_lines = [line] if line else []
    lines.extend(f"- {item}" for item in source_lines)

    focus_areas = _coerce_string_list(input_payload.get("focus_areas"))
    if focus_areas:
        lines.append("focus areas:")
        lines.extend(f"- {item}" for item in focus_areas)

    excluded_topics = _coerce_string_list(input_payload.get("excluded_topics"))
    if excluded_topics:
        lines.append("excluded topics:")
        lines.extend(f"- {item}" for item in excluded_topics)
    return "\n".join(lines)


def _readiness_check_notes(input_payload: dict[str, Any]) -> str:
    lines = [
        f"check_set: {input_payload.get('check_set')}",
        f"target_stage: {input_payload.get('target_stage')}",
        f"sensitivity: {input_payload.get('sensitivity')}",
        f"env_profile: {input_payload.get('env_profile', 'local')}",
        f"strict_gate: {input_payload.get('strict_gate', False)}",
        f"timeout_seconds: {input_payload.get('timeout_seconds', 'default')}",
        "readiness intent:",
        "- Summarize pass, skip, blocked, and next-action evidence for the requested check set.",
        "- Preserve external sandbox/live blockers as explicit readiness state rather than treating them as solved.",
    ]
    return "\n".join(lines)


def _job_template_task_kind(template: dict[str, Any]) -> str:
    submit_contract = dict(template.get("submit_contract") or {})
    return str(submit_contract.get("task_kind") or "task").strip().lower() or "task"


def _resolve_job_static_contract(*, template_id: str, profile_id: str) -> dict[str, Any]:
    templates_by_id, profiles_by_id, packs_by_id = _load_stage12_job_registries()

    template = templates_by_id.get(template_id)
    if template is None:
        raise ValueError(f"unknown job template: {template_id}")
    if not bool(template.get("enabled", True)):
        raise ValueError(f"job template is disabled: {template_id}")

    profile = profiles_by_id.get(profile_id)
    if profile is None:
        raise ValueError(f"unknown agent profile: {profile_id}")
    if not bool(profile.get("enabled", True)):
        raise ValueError(f"agent profile is disabled: {profile_id}")

    if profile_id not in list(template.get("allowed_profile_ids") or []):
        raise ValueError(f"job template {template_id} does not allow profile: {profile_id}")
    if template_id not in list(profile.get("allowed_job_templates") or []):
        raise ValueError(f"profile {profile_id} does not allow job template: {template_id}")

    provider_policy = dict(template.get("provider_policy") or {})
    provider_class = str(profile.get("provider_class") or "").strip()
    allowed_provider_classes = {str(item) for item in provider_policy.get("allowed_provider_classes") or []}
    if allowed_provider_classes and provider_class not in allowed_provider_classes:
        raise ValueError(f"template {template_id} does not allow provider class: {provider_class}")

    required_pack_ids = [str(item).strip() for item in template.get("required_capability_packs") or [] if str(item).strip()]
    if not required_pack_ids:
        raise ValueError(f"job template {template_id} has no required capability packs")
    profile_pack_ids = {str(item) for item in profile.get("allowed_capability_packs") or []}
    packs: list[dict[str, Any]] = []
    for pack_id in required_pack_ids:
        pack = packs_by_id.get(pack_id)
        if pack is None:
            raise ValueError(f"job template {template_id} references unknown capability pack: {pack_id}")
        if not bool(pack.get("enabled", True)):
            raise ValueError(f"capability pack is disabled: {pack_id}")
        if pack_id not in profile_pack_ids:
            raise ValueError(f"profile {profile_id} does not allow capability pack: {pack_id}")
        if profile_id not in list(pack.get("allowed_profile_ids") or []):
            raise ValueError(f"capability pack {pack_id} does not allow profile: {profile_id}")
        if template_id not in list(pack.get("allowed_template_ids") or []):
            raise ValueError(f"capability pack {pack_id} does not allow template: {template_id}")
        packs.append(pack)

    return {
        "template": template,
        "profile": profile,
        "packs": packs,
        "capability_pack_ids": required_pack_ids,
    }


def _validate_job_input_against_contract(
    *,
    template: dict[str, Any],
    profile: dict[str, Any],
    packs: list[dict[str, Any]],
    input_payload: dict[str, Any],
) -> None:
    schema = dict(template.get("input_schema") or {})
    required_fields = [str(item).strip() for item in schema.get("required_fields") or [] if str(item).strip()]
    missing = [field for field in required_fields if input_payload.get(field) in (None, "", [])]
    if missing:
        raise ValueError(f"job input missing required fields: {', '.join(missing)}")

    max_payload_bytes = int(schema.get("max_payload_bytes") or 0)
    if max_payload_bytes > 0:
        payload_bytes = len(json.dumps(input_payload, ensure_ascii=False).encode("utf-8"))
        if payload_bytes > max_payload_bytes:
            raise ValueError(f"job input exceeds max_payload_bytes: {payload_bytes} > {max_payload_bytes}")

    sensitivity_field = str(schema.get("sensitivity_field") or "sensitivity")
    sensitivity = str(input_payload.get(sensitivity_field) or "").strip()
    profile_sensitivity = dict(profile.get("sensitivity_boundary") or {})
    profile_allowed = {str(item) for item in profile_sensitivity.get("allowed_sensitivity") or []}
    if sensitivity and profile_allowed and sensitivity not in profile_allowed:
        raise ValueError(f"profile {profile.get('profile_id')} does not allow sensitivity: {sensitivity}")
    for pack in packs:
        pack_boundary = dict(pack.get("data_boundary") or {})
        pack_allowed = {str(item) for item in pack_boundary.get("allowed_sensitivity") or []}
        if sensitivity and pack_allowed and sensitivity not in pack_allowed:
            raise ValueError(f"capability pack {pack.get('pack_id')} does not allow sensitivity: {sensitivity}")


def _resolve_job_contract(
    *,
    template_id: str,
    profile_id: str,
    input_payload: dict[str, Any],
) -> dict[str, Any]:
    contract = _resolve_job_static_contract(template_id=template_id, profile_id=profile_id)
    template = dict(contract["template"])
    profile = dict(contract["profile"])
    packs = [dict(item) for item in contract["packs"]]

    _validate_job_input_against_contract(
        template=template,
        profile=profile,
        packs=packs,
        input_payload=input_payload,
    )
    return contract


def _stage12_job_metadata(contract: dict[str, Any]) -> dict[str, Any]:
    template = dict(contract["template"])
    profile = dict(contract["profile"])
    packs = [dict(item) for item in contract["packs"]]
    return {
        "template_id": template.get("template_id"),
        "profile_id": profile.get("profile_id"),
        "provider_id": profile.get("provider_id"),
        "provider_class": profile.get("provider_class"),
        "capability_pack_ids": list(contract["capability_pack_ids"]),
        "provider_policy": dict(template.get("provider_policy") or {}),
        "execution_budget": dict(template.get("execution_budget_override") or profile.get("execution_budget") or {}),
        "output_evidence": dict(template.get("output_evidence") or {}),
        "capability_packs": [
            {
                "pack_id": pack.get("pack_id"),
                "risk_level": pack.get("risk_level"),
                "allowed_tool_ids": list(pack.get("allowed_tool_ids") or []),
                "runtime_read_surfaces": list(pack.get("runtime_read_surfaces") or []),
                "external_send_policy": (pack.get("data_boundary") or {}).get("external_send_policy"),
            }
            for pack in packs
        ],
    }


def _job_runtime_metadata(contract: dict[str, Any], input_payload: dict[str, Any]) -> dict[str, Any]:
    template = dict(contract["template"])
    template_id = str(template.get("template_id") or "")
    stage12_job = _stage12_job_metadata(contract)
    if template_id == "daily_status_digest":
        audience = _coerce_string_list(input_payload.get("audience"), fallback=["operator"])
        return {
            "template_type": "meeting_summary",
            "meeting_title": str(template.get("display_name") or "Daily status digest"),
            "meeting_date": str(input_payload.get("date") or ""),
            "participants": audience,
            "notes": _daily_status_notes(input_payload),
            "sensitivity": str(input_payload.get("sensitivity") or ""),
            "stage12_job": stage12_job,
            "stage12_job_input": dict(input_payload),
        }
    if template_id == "readiness_check":
        return {
            "template_type": "meeting_summary",
            "meeting_title": str(template.get("display_name") or "Readiness check"),
            "meeting_date": datetime.now(timezone.utc).date().isoformat(),
            "participants": [str(input_payload.get("requested_by") or "operator")],
            "notes": _readiness_check_notes(input_payload),
            "sensitivity": str(input_payload.get("sensitivity") or ""),
            "stage12_job": stage12_job,
            "stage12_job_input": dict(input_payload),
        }
    raise ValueError(f"job template is not implemented in this PoC: {template_id}")


def _profile_compatibility(template_id: str, profile_id: str) -> dict[str, Any]:
    try:
        contract = _resolve_job_static_contract(template_id=template_id, profile_id=profile_id)
    except ValueError as exc:
        return {"profile_id": profile_id, "compatible": False, "reason": str(exc)}
    profile = dict(contract["profile"])
    return {
        "profile_id": profile_id,
        "compatible": True,
        "provider_id": profile.get("provider_id"),
        "provider_class": profile.get("provider_class"),
        "capability_pack_ids": list(contract["capability_pack_ids"]),
    }


def _job_template_discovery_item(template: dict[str, Any], *, profile_id: str | None = None) -> dict[str, Any]:
    template_id = str(template.get("template_id") or "")
    candidate_profile_ids = [str(item) for item in template.get("allowed_profile_ids") or []]
    if profile_id:
        candidate_profile_ids = [profile_id]
    compatibility = [_profile_compatibility(template_id, item) for item in candidate_profile_ids]
    compatible_profile_ids = [item["profile_id"] for item in compatibility if item.get("compatible")]
    submit_contract = dict(template.get("submit_contract") or {})
    return {
        "template_id": template_id,
        "display_name": template.get("display_name"),
        "description": template.get("description"),
        "enabled": bool(template.get("enabled", True)),
        "workflow_family": template.get("workflow_family"),
        "executable": template_id in IMPLEMENTED_JOB_TEMPLATE_IDS,
        "implemented_adapter": template_id if template_id in IMPLEMENTED_JOB_TEMPLATE_IDS else None,
        "task_kind": submit_contract.get("task_kind"),
        "required_capability_packs": list(template.get("required_capability_packs") or []),
        "compatible_profile_ids": compatible_profile_ids,
        "profile_compatibility": compatibility,
        "runtime_surfaces": {
            "submit": submit_contract.get("surface", "agent.submit"),
            "status": submit_contract.get("status_surface", "agent.status"),
            "events": submit_contract.get("events_surface", "agent.events"),
            "report": submit_contract.get("report_surface", "agent.report"),
            "bundle": "agent.bundle",
            "handoff": "agent.handoff",
        },
    }


def _job_list_payload(*, profile_id: str | None = None, include_disabled: bool = False) -> tuple[dict[str, Any], int]:
    try:
        return stage12_job_list_payload(profile_id=profile_id, include_disabled=include_disabled), 0
    except ValueError as exc:
        return _error_payload("INVALID_JOB_DISCOVERY", str(exc)), 1


def _job_describe_payload(*, template_id: str, profile_id: str | None = None) -> tuple[dict[str, Any], int]:
    try:
        return stage12_job_describe_payload(template_id=template_id, profile_id=profile_id), 0
    except ValueError as exc:
        return _error_payload("INVALID_JOB_DISCOVERY", str(exc)), 1


def _job_invocation_summary(
    *,
    contract: dict[str, Any],
    input_payload: dict[str, Any],
    requested_by: str,
    auto_run: bool,
) -> dict[str, Any]:
    template = dict(contract["template"])
    profile = dict(contract["profile"])
    packs = [dict(item) for item in contract["packs"]]
    status_contract = dict(template.get("submit_contract") or {})
    return {
        "command_surface": "newclaw job run",
        "template_id": template.get("template_id"),
        "template_display_name": template.get("display_name"),
        "profile_id": profile.get("profile_id"),
        "provider_id": profile.get("provider_id"),
        "provider_class": profile.get("provider_class"),
        "requested_by": requested_by,
        "auto_run": auto_run,
        "task_kind": _job_template_task_kind(template),
        "capability_pack_ids": list(contract["capability_pack_ids"]),
        "allowed_tool_ids": sorted(
            {
                str(tool_id)
                for pack in packs
                for tool_id in list(pack.get("allowed_tool_ids") or [])
                if str(tool_id).strip()
            }
        ),
        "runtime_surfaces": {
            "submit": status_contract.get("surface", "agent.submit"),
            "status": status_contract.get("status_surface", "agent.status"),
            "events": status_contract.get("events_surface", "agent.events"),
            "report": status_contract.get("report_surface", "agent.report"),
            "bundle": "agent.bundle",
            "handoff": "agent.handoff",
        },
        "input_schema": dict(template.get("input_schema") or {}),
        "input_keys": sorted(str(key) for key in input_payload.keys()),
        "provider_policy": dict(template.get("provider_policy") or {}),
        "execution_budget": dict(template.get("execution_budget_override") or profile.get("execution_budget") or {}),
    }


def _job_run_payload(
    *,
    template_id: str,
    profile_id: str,
    input_payload: dict[str, Any],
    requested_by: str,
    actor_id: str | None = None,
    actor_role: str = DEFAULT_ACTOR_ROLE,
    include_bundle: bool = False,
    include_handoff: bool = False,
    max_chars: int = 4000,
    auto_run: bool = True,
) -> tuple[dict[str, Any], int]:
    try:
        actor = _actor_context(actor_id or requested_by, actor_role)
        payload = run_stage12_job(
            orchestration_service=CLI_ORCHESTRATION_SERVICE,
            actor=actor,
            template_id=template_id,
            profile_id=profile_id,
            input_payload=input_payload,
            requested_by=requested_by,
            include_bundle=include_bundle,
            include_handoff=include_handoff,
            max_chars=max_chars,
            auto_run=auto_run,
        )
        return payload, 0
    except HTTPException as exc:
        return _coerce_http_error(exc), 1
    except ValueError as exc:
        return _error_payload("INVALID_JOB_CONTRACT", str(exc)), 1
    except Exception as exc:  # pragma: no cover - defensive
        return _error_payload("CLI_ERROR", str(exc)), 1


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


def _recent_payload(*, limit: int, actor_id: str, actor_role: str) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_ORCHESTRATION_SERVICE.agent_recent, actor, limit=limit)


def _report_payload(
    task_id: str,
    *,
    max_chars: int,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_ORCHESTRATION_SERVICE.agent_report, task_id, actor, max_chars=max_chars)


def _bundle_payload(
    task_id: str,
    *,
    max_chars: int,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_ORCHESTRATION_SERVICE.agent_bundle, task_id, actor, max_chars=max_chars)


def _handoff_payload(
    task_id: str,
    *,
    max_chars: int,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_ORCHESTRATION_SERVICE.agent_handoff, task_id, actor, max_chars=max_chars)


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


def _approvals_payload(
    *,
    status: str | None,
    approver_group: str | None,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_APPROVAL_SERVICE.list_approvals, status, approver_group, actor)


def _approval_detail_payload(
    queue_id: str,
    *,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_APPROVAL_SERVICE.get_approval, queue_id, actor)


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


def _capabilities_payload(
    *,
    actor_id: str,
    actor_role: str,
) -> tuple[dict[str, Any], int]:
    actor = _actor_context(actor_id, actor_role)
    return _invoke(CLI_CAPABILITY_MANIFEST_SERVICE.get_manifest, actor)


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


def _print_approval_detail(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    item = payload.get("item") or {}
    task_summary = payload.get("task_summary") or {}
    print("\n[승인 상세]")
    print(f"- Queue ID: {payload.get('queue_id', '-')}")
    print(f"- 승인 상태: {item.get('status', '-')}")
    print(f"- 사유: {item.get('reason_code', '-')}")
    print(f"- 요청자: {item.get('requested_by', '-')}")
    print(f"- Task ID: {task_summary.get('task_id', item.get('task_id', '-'))}")
    print(f"- Task 상태: {task_summary.get('status', '-')}")
    actions = payload.get("actions") or []
    if actions:
      print("- 이력:")
      for action in actions:
          line = f"  - {action.get('created_at', '-')} {action.get('action', '-')} by {action.get('acted_by', '-')}"
          if action.get("comment"):
              line += f" :: {action.get('comment')}"
          print(line)
    print()


def _print_approvals(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[승인 목록]")
    for item in payload.get("items", []):
        print(
            f"- {item.get('queue_id', '-')}: {item.get('status', '-')} / "
            f"{item.get('reason_code', '-')} / task={item.get('task_id', '-')}"
        )
    print()


def _print_recent(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[최근 작업]")
    for item in payload.get("items", []):
        state_summary = item.get("state_summary") or {}
        print(
            f"- {item.get('task_id', '-')}: {item.get('resolved_kind', '-')} / {item.get('status', '-')} / "
            f"{item.get('title', '-')} / {state_summary.get('canonical_reason_code', '-')}"
        )
    print()


def _print_report(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[보고서 미리보기]")
    print(f"- Task ID: {payload.get('task_id', '-')}")
    print(f"- 종류: {payload.get('resolved_kind', '-')}")
    print(f"- 상태: {payload.get('status', '-')}")
    print(f"- 파일: {payload.get('report_path', '-')}")
    print(f"- Raw URL: {payload.get('raw_url', '-')}")
    print()
    print(payload.get("preview_text", ""))
    print()


def _print_bundle(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[실행 번들]")
    print(f"- Task ID: {payload.get('task_id', '-')}")
    print(f"- 종류: {payload.get('resolved_kind', '-')}")
    status_payload = payload.get("status") or {}
    state_summary = status_payload.get("state_summary") or {}
    print(f"- 상태: {status_payload.get('status', '-')}")
    print(f"- Canonical state/reason: {state_summary.get('canonical_state', '-')} / {state_summary.get('canonical_reason_code', '-')}")
    approval = payload.get("approval") or {}
    print(f"- Approval access: {approval.get('access_level', '-')}")
    print(f"- Event count: {((payload.get('events') or {}).get('count')) or 0}")
    report = payload.get("report") or {}
    if report.get("available"):
        print(f"- Report: {report.get('report_name', '-')}")
    else:
        print(f"- Report: {report.get('reason', 'not_ready')}")
    capabilities = ((payload.get("capabilities") or {}).get("snapshot") or {})
    print(f"- Product posture: {capabilities.get('product_posture', '-')}")
    print()


def _print_handoff(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    markdown = str(payload.get("markdown") or "").strip()
    if markdown:
        print()
        print(markdown)
        return
    print("\n[운영자 인계 패킷]")
    print(f"- Task ID: {payload.get('task_id', '-')}")
    print(f"- Packet type: {payload.get('packet_type', '-')}")
    print(f"- Recommended owner: {payload.get('recommended_handoff_owner', '-')}")
    print()


def _print_job_run(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    invocation = payload.get("job_invocation") or {}
    status = payload.get("status") or {}
    events = payload.get("events") or {}
    report = payload.get("report") or {}
    print("\n[Stage 12 Job Run]")
    print(f"- Template: {invocation.get('template_id', '-')}")
    print(f"- Profile: {invocation.get('profile_id', '-')}")
    print(f"- Provider: {invocation.get('provider_id', '-')} ({invocation.get('provider_class', '-')})")
    print(f"- Task ID: {invocation.get('task_id', status.get('task_id', '-'))}")
    print(f"- Status: {status.get('status', '-')}")
    print(f"- Events: {events.get('count', 0)}")
    if report.get("available"):
        print(f"- Report: {report.get('report_path', '-')}")
    print(f"- Capability Packs: {', '.join(invocation.get('capability_pack_ids') or []) or '-'}")
    print()


def _print_job_list(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[Stage 12 Job Templates]")
    for item in payload.get("items", []):
        status = "executable" if item.get("executable") else "planned"
        profiles = ", ".join(item.get("compatible_profile_ids") or []) or "-"
        print(f"- {item.get('template_id', '-')}: {status} / profiles={profiles}")
    print()


def _print_job_describe(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    template = payload.get("template") or {}
    print("\n[Stage 12 Job Template]")
    print(f"- Template: {template.get('template_id', '-')}")
    print(f"- Display: {template.get('display_name', '-')}")
    print(f"- Executable: {template.get('executable', False)}")
    print(f"- Required packs: {', '.join(template.get('required_capability_packs') or []) or '-'}")
    print(f"- Compatible profiles: {', '.join(template.get('compatible_profile_ids') or []) or '-'}")
    examples = payload.get("examples") or []
    if examples:
        print(f"- Example: {examples[0]}")
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


def _print_capabilities(payload: dict[str, Any]) -> None:
    if "error" in payload:
        _print_status(payload)
        return
    print("\n[Capability Manifest]")
    print(f"- Product posture: {payload.get('product_posture', '-')}")
    print(f"- Primary entrypoint: {payload.get('primary_entrypoint', '-')}")
    print(f"- Roles: {', '.join(payload.get('roles', [])) or '-'}")
    tool_catalog = payload.get("tool_catalog") or {}
    print(f"- Tool count: {tool_catalog.get('count', '-')}")
    mcp_transport = (payload.get("transport") or {}).get("mcp") or {}
    print(f"- MCP transport: {mcp_transport.get('baseline', '-')}")
    readiness = (payload.get("readiness") or {}).get("stage8_live_readiness") or {}
    print(f"- Stage8 live readiness: {readiness.get('status', '-')}")
    print(f"- Readiness reason: {readiness.get('canonical_reason_code', '-')}")
    missing = readiness.get("missing_env") or []
    if missing:
        print(f"- Missing env: {', '.join(missing)}")
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
    if command == "capabilities":
        _print_capabilities(payload)
        return
    if command == "recent":
        _print_recent(payload)
        return
    if command == "report":
        _print_report(payload)
        return
    if command == "bundle":
        _print_bundle(payload)
        return
    if command == "handoff":
        _print_handoff(payload)
        return
    if command == "job-run":
        _print_job_run(payload)
        return
    if command == "job-list":
        _print_job_list(payload)
        return
    if command == "job-describe":
        _print_job_describe(payload)
        return
    if command == "approvals":
        _print_approvals(payload)
        return
    if command == "approval-get":
        _print_approval_detail(payload)
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

    job_parser = subparsers.add_parser("job", help="run Stage 12 job templates")
    job_subparsers = job_parser.add_subparsers(dest="job_command")
    job_list_parser = job_subparsers.add_parser("list", help="list Stage 12 job templates")
    job_list_parser.add_argument("--profile", dest="profile_id")
    job_list_parser.add_argument("--include-disabled", action="store_true")
    job_list_parser.add_argument("--json", action="store_true")

    job_describe_parser = job_subparsers.add_parser("describe", help="describe one Stage 12 job template")
    job_describe_parser.add_argument("--template", dest="template_id", required=True)
    job_describe_parser.add_argument("--profile", dest="profile_id")
    job_describe_parser.add_argument("--json", action="store_true")

    job_run_parser = job_subparsers.add_parser("run", help="run one bounded job template")
    job_run_parser.add_argument("--template", dest="template_id", required=True)
    job_run_parser.add_argument("--profile", dest="profile_id", required=True)
    job_input_group = job_run_parser.add_mutually_exclusive_group(required=True)
    job_input_group.add_argument("--input-json")
    job_input_group.add_argument("--input-file", "--input", dest="input_file")
    job_run_parser.add_argument("--requested-by", required=True)
    job_run_parser.add_argument("--actor-id")
    job_run_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    job_run_parser.add_argument("--include-bundle", action="store_true")
    job_run_parser.add_argument("--include-handoff", action="store_true")
    job_run_parser.add_argument("--max-chars", type=int, default=4000)
    job_run_parser.add_argument("--no-auto-run", action="store_true")
    job_run_parser.add_argument("--json", action="store_true")

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

    recent_parser = subparsers.add_parser("recent", help="show recent agent tasks")
    recent_parser.add_argument("--limit", type=int, default=10)
    recent_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    recent_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    recent_parser.add_argument("--json", action="store_true")

    report_parser = subparsers.add_parser("report", help="show agent report preview")
    report_parser.add_argument("--task-id", required=True)
    report_parser.add_argument("--max-chars", type=int, default=4000)
    report_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    report_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    report_parser.add_argument("--json", action="store_true")

    bundle_parser = subparsers.add_parser("bundle", help="show a canonical execution bundle for one agent task")
    bundle_parser.add_argument("--task-id", required=True)
    bundle_parser.add_argument("--max-chars", type=int, default=4000)
    bundle_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    bundle_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    bundle_parser.add_argument("--json", action="store_true")

    handoff_parser = subparsers.add_parser("handoff", help="show a compact operator handoff packet for one agent task")
    handoff_parser.add_argument("--task-id", required=True)
    handoff_parser.add_argument("--max-chars", type=int, default=1600)
    handoff_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    handoff_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    handoff_parser.add_argument("--json", action="store_true")

    approvals_parser = subparsers.add_parser("approvals", help="list approval queue items")
    approvals_parser.add_argument("--status")
    approvals_parser.add_argument("--approver-group")
    approvals_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    approvals_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default="approver")
    approvals_parser.add_argument("--json", action="store_true")

    approval_get_parser = subparsers.add_parser("approval-get", help="show one approval queue item")
    approval_get_parser.add_argument("--queue-id", required=True)
    approval_get_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    approval_get_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default="approver")
    approval_get_parser.add_argument("--json", action="store_true")

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

    capabilities_parser = subparsers.add_parser("capabilities", help="show current orchestration capability manifest")
    capabilities_parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID)
    capabilities_parser.add_argument("--actor-role", choices=sorted(VALID_ROLES), default=DEFAULT_ACTOR_ROLE)
    capabilities_parser.add_argument("--json", action="store_true")

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

    if args.command == "job":
        if args.job_command == "list":
            payload, exit_code = _job_list_payload(
                profile_id=args.profile_id,
                include_disabled=args.include_disabled,
            )
            _emit_payload(payload, as_json=args.json, command="job-list")
            return exit_code
        if args.job_command == "describe":
            payload, exit_code = _job_describe_payload(
                template_id=args.template_id,
                profile_id=args.profile_id,
            )
            _emit_payload(payload, as_json=args.json, command="job-describe")
            return exit_code
        if args.job_command != "run":
            parser.print_help()
            return 2
        input_payload, input_rc = _job_input_payload(args.input_json, args.input_file)
        if input_rc != 0:
            _emit_payload(input_payload, as_json=args.json, command="job-run")
            return input_rc
        payload, exit_code = _job_run_payload(
            template_id=args.template_id,
            profile_id=args.profile_id,
            input_payload=input_payload,
            requested_by=args.requested_by,
            actor_id=args.actor_id or args.requested_by,
            actor_role=args.actor_role,
            include_bundle=args.include_bundle,
            include_handoff=args.include_handoff,
            max_chars=args.max_chars,
            auto_run=not args.no_auto_run,
        )
        _emit_payload(payload, as_json=args.json, command="job-run")
        return exit_code

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

    if args.command == "recent":
        payload, exit_code = _recent_payload(limit=args.limit, actor_id=args.actor_id, actor_role=args.actor_role)
        _emit_payload(payload, as_json=args.json, command="recent")
        return exit_code

    if args.command == "report":
        payload, exit_code = _report_payload(
            args.task_id,
            max_chars=args.max_chars,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="report")
        return exit_code

    if args.command == "bundle":
        payload, exit_code = _bundle_payload(
            args.task_id,
            max_chars=args.max_chars,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="bundle")
        return exit_code

    if args.command == "handoff":
        payload, exit_code = _handoff_payload(
            args.task_id,
            max_chars=args.max_chars,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="handoff")
        return exit_code

    if args.command == "approvals":
        payload, exit_code = _approvals_payload(
            status=args.status,
            approver_group=args.approver_group,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="approvals")
        return exit_code

    if args.command == "approval-get":
        payload, exit_code = _approval_detail_payload(
            args.queue_id,
            actor_id=args.actor_id,
            actor_role=args.actor_role,
        )
        _emit_payload(payload, as_json=args.json, command="approval-get")
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

    if args.command == "capabilities":
        payload, exit_code = _capabilities_payload(actor_id=args.actor_id, actor_role=args.actor_role)
        _emit_payload(payload, as_json=args.json, command="capabilities")
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
