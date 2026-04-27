from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


AGENT_PROFILES_PATH = Path("configs/agent_profiles.json")
JOB_TEMPLATES_PATH = Path("configs/job_templates.json")
CAPABILITY_PACKS_PATH = Path("configs/capability_packs.json")
IMPLEMENTED_JOB_TEMPLATE_IDS = {"daily_status_digest", "readiness_check"}


def load_json_document(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"registry file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json registry {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"registry must be a JSON object: {path}")
    return payload


def registry_items_by_id(path: Path, collection_key: str, id_key: str) -> dict[str, dict[str, Any]]:
    document = load_json_document(path)
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


def load_stage12_job_registries() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    return (
        registry_items_by_id(JOB_TEMPLATES_PATH, "templates", "template_id"),
        registry_items_by_id(AGENT_PROFILES_PATH, "profiles", "profile_id"),
        registry_items_by_id(CAPABILITY_PACKS_PATH, "packs", "pack_id"),
    )


def coerce_string_list(value: Any, *, fallback: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    elif value is None:
        items = []
    else:
        items = [str(value).strip()]
    return items or list(fallback or [])


def source_line(source: Any) -> str:
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


def daily_status_notes(input_payload: dict[str, Any]) -> str:
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
            line = source_line(item)
            if line:
                source_lines.append(line)
    else:
        line = source_line(sources)
        source_lines = [line] if line else []
    lines.extend(f"- {item}" for item in source_lines)

    focus_areas = coerce_string_list(input_payload.get("focus_areas"))
    if focus_areas:
        lines.append("focus areas:")
        lines.extend(f"- {item}" for item in focus_areas)

    excluded_topics = coerce_string_list(input_payload.get("excluded_topics"))
    if excluded_topics:
        lines.append("excluded topics:")
        lines.extend(f"- {item}" for item in excluded_topics)
    return "\n".join(lines)


def readiness_check_notes(input_payload: dict[str, Any]) -> str:
    return "\n".join(
        [
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
    )


def job_template_task_kind(template: dict[str, Any]) -> str:
    submit_contract = dict(template.get("submit_contract") or {})
    return str(submit_contract.get("task_kind") or "task").strip().lower() or "task"


def resolve_job_static_contract(*, template_id: str, profile_id: str) -> dict[str, Any]:
    templates_by_id, profiles_by_id, packs_by_id = load_stage12_job_registries()

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


def validate_job_input_against_contract(
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


def resolve_job_contract(*, template_id: str, profile_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    contract = resolve_job_static_contract(template_id=template_id, profile_id=profile_id)
    validate_job_input_against_contract(
        template=dict(contract["template"]),
        profile=dict(contract["profile"]),
        packs=[dict(item) for item in contract["packs"]],
        input_payload=input_payload,
    )
    return contract


def stage12_job_metadata(contract: dict[str, Any]) -> dict[str, Any]:
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


def job_runtime_metadata(contract: dict[str, Any], input_payload: dict[str, Any]) -> dict[str, Any]:
    template = dict(contract["template"])
    template_id = str(template.get("template_id") or "")
    stage12_job = stage12_job_metadata(contract)
    if template_id == "daily_status_digest":
        audience = coerce_string_list(input_payload.get("audience"), fallback=["operator"])
        return {
            "template_type": "meeting_summary",
            "meeting_title": str(template.get("display_name") or "Daily status digest"),
            "meeting_date": str(input_payload.get("date") or ""),
            "participants": audience,
            "notes": daily_status_notes(input_payload),
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
            "notes": readiness_check_notes(input_payload),
            "sensitivity": str(input_payload.get("sensitivity") or ""),
            "stage12_job": stage12_job,
            "stage12_job_input": dict(input_payload),
        }
    raise ValueError(f"job template is not implemented in this PoC: {template_id}")


def job_invocation_summary(
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
        "task_kind": job_template_task_kind(template),
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


def profile_compatibility(template_id: str, profile_id: str) -> dict[str, Any]:
    try:
        contract = resolve_job_static_contract(template_id=template_id, profile_id=profile_id)
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


def job_template_discovery_item(template: dict[str, Any], *, profile_id: str | None = None) -> dict[str, Any]:
    template_id = str(template.get("template_id") or "")
    candidate_profile_ids = [str(item) for item in template.get("allowed_profile_ids") or []]
    if profile_id:
        candidate_profile_ids = [profile_id]
    compatibility = [profile_compatibility(template_id, item) for item in candidate_profile_ids]
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


def job_list_payload(*, profile_id: str | None = None, include_disabled: bool = False) -> dict[str, Any]:
    templates_by_id, profiles_by_id, _ = load_stage12_job_registries()
    if profile_id and profile_id not in profiles_by_id:
        raise ValueError(f"unknown agent profile: {profile_id}")
    items = []
    for template in templates_by_id.values():
        if not include_disabled and not bool(template.get("enabled", True)):
            continue
        item = job_template_discovery_item(template, profile_id=profile_id)
        if profile_id and not item["profile_compatibility"]:
            continue
        items.append(item)
    items.sort(key=lambda item: str(item.get("template_id") or ""))
    return {
        "surface": "newclaw job list",
        "items": items,
        "count": len(items),
        "profile_filter": profile_id,
        "implemented_job_template_ids": sorted(IMPLEMENTED_JOB_TEMPLATE_IDS),
    }


def job_describe_payload(*, template_id: str, profile_id: str | None = None) -> dict[str, Any]:
    templates_by_id, profiles_by_id, packs_by_id = load_stage12_job_registries()
    template = templates_by_id.get(template_id)
    if template is None:
        raise ValueError(f"unknown job template: {template_id}")
    if profile_id and profile_id not in profiles_by_id:
        raise ValueError(f"unknown agent profile: {profile_id}")
    item = job_template_discovery_item(template, profile_id=profile_id)
    required_pack_ids = [str(pack_id) for pack_id in template.get("required_capability_packs") or []]
    packs = [packs_by_id[pack_id] for pack_id in required_pack_ids if pack_id in packs_by_id]
    examples = list((template.get("schedule_trigger") or {}).get("examples") or [])
    if not examples:
        examples = [f"newclaw job run --template {template_id} --profile <profile_id> --input-file <input.json> --json"]
    return {
        "surface": "newclaw job describe",
        "template": item,
        "input_schema": dict(template.get("input_schema") or {}),
        "provider_policy": dict(template.get("provider_policy") or {}),
        "execution_budget_override": dict(template.get("execution_budget_override") or {}),
        "approval_requirements": dict(template.get("approval_requirements") or {}),
        "schedule_trigger": dict(template.get("schedule_trigger") or {}),
        "output_evidence": dict(template.get("output_evidence") or {}),
        "capability_packs": [
            {
                "pack_id": pack.get("pack_id"),
                "display_name": pack.get("display_name"),
                "risk_level": pack.get("risk_level"),
                "pack_type": pack.get("pack_type"),
                "allowed_tool_ids": list(pack.get("allowed_tool_ids") or []),
                "runtime_read_surfaces": list(pack.get("runtime_read_surfaces") or []),
                "approval_requirements": dict(pack.get("approval_requirements") or {}),
                "data_boundary": dict(pack.get("data_boundary") or {}),
            }
            for pack in packs
        ],
        "examples": examples,
    }


def build_job_submit_payload(
    *,
    template_id: str,
    profile_id: str,
    input_payload: dict[str, Any],
    requested_by: str,
    auto_run: bool = True,
) -> dict[str, Any]:
    contract = resolve_job_contract(template_id=template_id, profile_id=profile_id, input_payload=input_payload)
    metadata = job_runtime_metadata(contract, input_payload)
    invocation = job_invocation_summary(
        contract=contract,
        input_payload=input_payload,
        requested_by=requested_by,
        auto_run=auto_run,
    )
    template = dict(contract["template"])
    description = str(template.get("description") or template.get("display_name") or template_id)
    return {
        "job_invocation": invocation,
        "submit_payload": {
            "request_text": f"Run Stage 12 job `{template_id}` for `{requested_by}`. {description}",
            "requested_by": requested_by,
            "task_kind": job_template_task_kind(template),
            "title": str(template.get("display_name") or template_id),
            "metadata": metadata,
            "auto_run": auto_run,
            "incident_run_mode": "dry-run",
        },
    }


def run_stage12_job(
    *,
    orchestration_service: Any,
    actor: Any,
    template_id: str,
    profile_id: str,
    input_payload: dict[str, Any],
    requested_by: str,
    include_bundle: bool = False,
    include_handoff: bool = False,
    max_chars: int = 4000,
    auto_run: bool = True,
) -> dict[str, Any]:
    built = build_job_submit_payload(
        template_id=template_id,
        profile_id=profile_id,
        input_payload=input_payload,
        requested_by=requested_by,
        auto_run=auto_run,
    )
    invocation = dict(built["job_invocation"])
    status_payload = orchestration_service.submit_agent(dict(built["submit_payload"]), actor)
    task_id = str(status_payload.get("task_id") or "")
    invocation["task_id"] = task_id
    events_payload = orchestration_service.agent_events(task_id, actor)

    report_payload: dict[str, Any] = {
        "available": False,
        "reason": "not_requested_until_done",
    }
    if status_payload.get("status") == "DONE":
        report_payload = orchestration_service.agent_report(task_id, actor, max_chars=max_chars)

    payload: dict[str, Any] = {
        "job_invocation": invocation,
        "status": status_payload,
        "events": events_payload,
        "report": report_payload,
    }
    if include_bundle:
        payload["bundle"] = orchestration_service.agent_bundle(task_id, actor, max_chars=max_chars)
    if include_handoff:
        payload["handoff"] = orchestration_service.agent_handoff(task_id, actor, max_chars=max_chars)
    return payload
