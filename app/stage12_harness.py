from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.validate_stage12_llm_harness import (
    DEFAULT_AGENT_PROFILES,
    DEFAULT_CAPABILITY_PACKS,
    DEFAULT_JOB_TEMPLATES,
    DEFAULT_MODEL_REGISTRY,
    HarnessValidator,
    parse_simple_yaml,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    boundary = dict(profile.get("sensitivity_boundary") or {})
    budget = dict(profile.get("execution_budget") or {})
    return {
        "profile_id": profile.get("profile_id"),
        "provider_id": profile.get("provider_id"),
        "provider_class": profile.get("provider_class"),
        "enabled": bool(profile.get("enabled", True)),
        "allowed_job_templates": list(profile.get("allowed_job_templates") or []),
        "allowed_capability_packs": list(profile.get("allowed_capability_packs") or []),
        "allowed_sensitivity": list(boundary.get("allowed_sensitivity") or []),
        "external_send_policy": boundary.get("external_send_policy"),
        "allow_network": bool(budget.get("allow_network")),
        "audit_level": profile.get("audit_level"),
    }


def _job_summary(template: dict[str, Any]) -> dict[str, Any]:
    schedule = dict(template.get("schedule_trigger") or {})
    idempotency_policy = dict(schedule.get("idempotency_key_policy") or {})
    return {
        "template_id": template.get("template_id"),
        "display_name": template.get("display_name"),
        "enabled": bool(template.get("enabled", True)),
        "workflow_family": template.get("workflow_family"),
        "allowed_profile_ids": list(template.get("allowed_profile_ids") or []),
        "required_capability_packs": list(template.get("required_capability_packs") or []),
        "supported_triggers": list(schedule.get("supported_triggers") or []),
        "idempotency_key_fields": list(schedule.get("idempotency_key_fields") or []),
        "idempotency_key_examples": list(idempotency_policy.get("examples") or []),
        "recommended_duplicate_policy": idempotency_policy.get("recommended_duplicate_policy"),
    }


def _pack_summary(pack: dict[str, Any]) -> dict[str, Any]:
    approval = dict(pack.get("approval_requirements") or {})
    boundary = dict(pack.get("data_boundary") or {})
    return {
        "pack_id": pack.get("pack_id"),
        "pack_type": pack.get("pack_type"),
        "risk_level": pack.get("risk_level"),
        "allowed_tool_count": len(list(pack.get("allowed_tool_ids") or [])),
        "runtime_read_surfaces": list(pack.get("runtime_read_surfaces") or []),
        "tool_write": approval.get("tool_write"),
        "external_send": approval.get("external_send"),
        "external_send_policy": boundary.get("external_send_policy"),
        "allowed_profile_ids": list(pack.get("allowed_profile_ids") or []),
        "allowed_template_ids": list(pack.get("allowed_template_ids") or []),
    }


def stage12_harness_status_payload() -> dict[str, Any]:
    profiles_doc = _load_json(DEFAULT_AGENT_PROFILES)
    jobs_doc = _load_json(DEFAULT_JOB_TEMPLATES)
    packs_doc = _load_json(DEFAULT_CAPABILITY_PACKS)
    model_doc = parse_simple_yaml(DEFAULT_MODEL_REGISTRY.read_text(encoding="utf-8"))

    validator = HarnessValidator(
        profiles_path=DEFAULT_AGENT_PROFILES,
        jobs_path=DEFAULT_JOB_TEMPLATES,
        packs_path=DEFAULT_CAPABILITY_PACKS,
        model_registry_path=DEFAULT_MODEL_REGISTRY,
    )
    validation = validator.validate()
    strict_status = "PASS" if validation["status"] == "PASS" and not validation["warnings"] else "FAIL"

    profiles = list(profiles_doc.get("profiles") or [])
    templates = list(jobs_doc.get("templates") or [])
    packs = list(packs_doc.get("packs") or [])
    providers = list(model_doc.get("providers") or [])
    local_profiles = [profile for profile in profiles if profile.get("provider_class") == "local_llm"]
    cloud_profiles = [profile for profile in profiles if profile.get("provider_class") == "cloud_api_llm"]

    return {
        "surface": "stage12.llm_harness",
        "status": strict_status,
        "validation": {
            "status": validation["status"],
            "strict_status": strict_status,
            "errors": list(validation["errors"]),
            "warnings": list(validation["warnings"]),
        },
        "counts": {
            "profiles": len(profiles),
            "local_profiles": len(local_profiles),
            "cloud_profiles": len(cloud_profiles),
            "job_templates": len(templates),
            "capability_packs": len(packs),
            "model_providers": len(providers),
        },
        "providers": [
            {
                "provider_id": provider.get("id"),
                "type": provider.get("type"),
                "engine": provider.get("engine"),
                "model": provider.get("model"),
                "enabled": bool(provider.get("enabled", True)),
            }
            for provider in providers
        ],
        "profiles": [_profile_summary(profile) for profile in profiles],
        "job_templates": [_job_summary(template) for template in templates],
        "capability_packs": [_pack_summary(pack) for pack in packs],
        "onboarding": {
            "primary_local_profile": "local_ollama_ops",
            "primary_local_provider": "local_primary",
            "guide": "NESTCLAW_LOCAL_LLM_PROVIDER_ONBOARDING_GUIDE_2026-04-29.md",
            "smoke_script": "scripts/run_stage12_local_llm_onboarding_smoke.sh",
        },
    }
