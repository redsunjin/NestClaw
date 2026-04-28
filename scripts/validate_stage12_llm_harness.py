from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT_PROFILES = ROOT / "configs" / "agent_profiles.json"
DEFAULT_JOB_TEMPLATES = ROOT / "configs" / "job_templates.json"
DEFAULT_CAPABILITY_PACKS = ROOT / "configs" / "capability_packs.json"
DEFAULT_MODEL_REGISTRY = ROOT / "configs" / "model_registry.yaml"

LOCAL_PROVIDER_TYPES = {"local"}
CLOUD_PROVIDER_TYPES = {"api", "cloud", "cloud_api"}
UPPER_PROVIDER_TYPES = {"upper_agent", "wrapper", "external_agent"}
FALLBACK_PROVIDER_TYPES = {"deterministic", "fallback"}
SENSITIVE_VALUES = {"sensitive_internal", "secret", "confidential", "high"}
SAFE_CLOUD_SENSITIVITY = {"public", "low", "redacted_metadata"}
ALLOWED_PROVIDER_CLASSES = {
    "local_llm",
    "cloud_api_llm",
    "upper_agent_wrapper",
    "deterministic_fallback",
}


def parse_scalar(value: str) -> Any:
    raw = value.strip()
    if not raw:
        return ""
    if raw in {"true", "True"}:
        return True
    if raw in {"false", "False"}:
        return False
    if raw in {"null", "None", "~"}:
        return None
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        return raw


def parse_key_value(raw: str) -> tuple[str, Any]:
    if ":" not in raw:
        raise ValueError(f"expected key/value line: {raw}")
    key, value = raw.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"empty key in line: {raw}")
    return key, parse_scalar(value)


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the limited YAML shape used by configs/model_registry.yaml.

    This intentionally avoids a PyYAML dependency so the harness validator can
    run in the lightweight system Python used by static contract gates.
    """

    document: dict[str, Any] = {}
    current_section: str | None = None
    current_item: dict[str, Any] | None = None
    current_nested: str | None = None

    for raw_line in text.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment.strip():
            continue
        indent = len(line_without_comment) - len(line_without_comment.lstrip(" "))
        stripped = line_without_comment.strip()

        if indent == 0:
            key, value = parse_key_value(stripped)
            if value == "":
                document[key] = []
                current_section = key
            else:
                document[key] = value
                current_section = None
            current_item = None
            current_nested = None
            continue

        if current_section is None:
            raise ValueError(f"nested line without section: {raw_line}")

        if indent == 2 and stripped.startswith("- "):
            if not isinstance(document.get(current_section), list):
                raise ValueError(f"section is not a list: {current_section}")
            current_item = {}
            document[current_section].append(current_item)
            current_nested = None
            rest = stripped[2:].strip()
            if rest:
                key, value = parse_key_value(rest)
                if value == "":
                    current_item[key] = {}
                    current_nested = key
                else:
                    current_item[key] = value
            continue

        if current_item is None:
            raise ValueError(f"item field without item: {raw_line}")

        if indent == 4:
            key, value = parse_key_value(stripped)
            if value == "":
                current_item[key] = {}
                current_nested = key
            else:
                current_item[key] = value
                current_nested = None
            continue

        if indent == 6 and current_nested:
            nested = current_item.get(current_nested)
            if not isinstance(nested, dict):
                raise ValueError(f"nested target is not an object: {current_nested}")
            key, value = parse_key_value(stripped)
            nested[key] = value
            continue

        raise ValueError(f"unsupported YAML shape: {raw_line}")

    return document


class HarnessValidator:
    def __init__(
        self,
        *,
        profiles_path: Path,
        jobs_path: Path,
        packs_path: Path,
        model_registry_path: Path,
    ) -> None:
        self.profiles_path = profiles_path
        self.jobs_path = jobs_path
        self.packs_path = packs_path
        self.model_registry_path = model_registry_path
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def load_json(self, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.error(f"missing file: {path}")
            return {}
        except json.JSONDecodeError as exc:
            self.error(f"invalid json: {path}: {exc}")
            return {}
        if not isinstance(payload, dict):
            self.error(f"expected json object: {path}")
            return {}
        return payload

    def load_yaml(self, path: Path) -> dict[str, Any]:
        try:
            payload = parse_simple_yaml(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.error(f"missing file: {path}")
            return {}
        except ValueError as exc:
            self.error(f"invalid yaml: {path}: {exc}")
            return {}
        if not isinstance(payload, dict):
            self.error(f"expected yaml object: {path}")
            return {}
        return payload

    def by_id(self, items: Any, id_key: str, label: str) -> dict[str, dict[str, Any]]:
        if not isinstance(items, list):
            self.error(f"{label}: expected list")
            return {}
        result: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                self.error(f"{label}: item must be object")
                continue
            item_id = str(item.get(id_key) or "").strip()
            if not item_id:
                self.error(f"{label}: item missing {id_key}")
                continue
            if item_id in result:
                self.error(f"{label}: duplicate id {item_id}")
                continue
            result[item_id] = item
        return result

    def string_set(self, value: Any) -> set[str]:
        if not isinstance(value, list):
            return set()
        return {str(item).strip() for item in value if str(item).strip()}

    def validate(self) -> dict[str, Any]:
        profiles_doc = self.load_json(self.profiles_path)
        jobs_doc = self.load_json(self.jobs_path)
        packs_doc = self.load_json(self.packs_path)
        model_doc = self.load_yaml(self.model_registry_path)

        profiles = self.by_id(profiles_doc.get("profiles"), "profile_id", "agent_profiles")
        jobs = self.by_id(jobs_doc.get("templates"), "template_id", "job_templates")
        packs = self.by_id(packs_doc.get("packs"), "pack_id", "capability_packs")
        providers = self.by_id(model_doc.get("providers"), "id", "model_registry.providers")

        self.validate_profiles(profiles, jobs, packs, providers)
        self.validate_jobs(jobs, profiles, packs)
        self.validate_packs(packs, profiles, jobs)
        self.validate_provider_routes(model_doc, providers)

        return {
            "surface": "stage12.llm_harness_validator",
            "status": "PASS" if not self.errors else "FAIL",
            "counts": {
                "profiles": len(profiles),
                "job_templates": len(jobs),
                "capability_packs": len(packs),
                "model_providers": len(providers),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "paths": {
                "agent_profiles": str(self.profiles_path),
                "job_templates": str(self.jobs_path),
                "capability_packs": str(self.packs_path),
                "model_registry": str(self.model_registry_path),
            },
        }

    def validate_profiles(
        self,
        profiles: dict[str, dict[str, Any]],
        jobs: dict[str, dict[str, Any]],
        packs: dict[str, dict[str, Any]],
        providers: dict[str, dict[str, Any]],
    ) -> None:
        for profile_id, profile in profiles.items():
            provider_id = str(profile.get("provider_id") or "").strip()
            provider_class = str(profile.get("provider_class") or "").strip()
            if provider_class not in ALLOWED_PROVIDER_CLASSES:
                self.error(f"profile {profile_id}: unsupported provider_class {provider_class}")
            if provider_id not in providers and provider_id not in {"upper_agent_wrapper", "deterministic_fallback"}:
                self.error(f"profile {profile_id}: provider_id not found in model registry: {provider_id}")
            if provider_id in providers:
                self.validate_provider_class_match(profile_id, provider_class, providers[provider_id])

            allowed_jobs = self.string_set(profile.get("allowed_job_templates"))
            allowed_packs = self.string_set(profile.get("allowed_capability_packs"))
            if not allowed_jobs:
                self.error(f"profile {profile_id}: allowed_job_templates must not be empty")
            if not allowed_packs:
                self.error(f"profile {profile_id}: allowed_capability_packs must not be empty")
            for template_id in allowed_jobs:
                if template_id not in jobs:
                    self.warn(f"profile {profile_id}: references future or missing job template {template_id}")
            for pack_id in allowed_packs:
                if pack_id not in packs:
                    self.error(f"profile {profile_id}: unknown capability pack {pack_id}")

            budget = dict(profile.get("execution_budget") or {})
            for key in ("max_tool_calls", "max_retries", "max_elapsed_seconds", "max_provider_tokens", "max_context_bytes"):
                if key not in budget:
                    self.error(f"profile {profile_id}: execution_budget missing {key}")
                    continue
                try:
                    if int(budget.get(key) or 0) < 0:
                        self.error(f"profile {profile_id}: execution_budget {key} must be non-negative")
                except (TypeError, ValueError):
                    self.error(f"profile {profile_id}: execution_budget {key} must be integer")

            boundary = dict(profile.get("sensitivity_boundary") or {})
            allowed_sensitivity = self.string_set(boundary.get("allowed_sensitivity"))
            external_policy = str(boundary.get("external_send_policy") or "").strip()
            approval = dict(profile.get("approval_policy") or {})

            if provider_class == "local_llm":
                if external_policy != "deny":
                    self.error(f"profile {profile_id}: local_llm external_send_policy must be deny")
                if bool(budget.get("allow_network")):
                    self.error(f"profile {profile_id}: local_llm execution_budget.allow_network must be false")
                if approval.get("external_send") != "blocked":
                    self.error(f"profile {profile_id}: local_llm approval_policy.external_send must be blocked")
            elif provider_class == "cloud_api_llm":
                if allowed_sensitivity - SAFE_CLOUD_SENSITIVITY:
                    self.error(
                        f"profile {profile_id}: cloud_api_llm allows unsafe sensitivity "
                        + ",".join(sorted(allowed_sensitivity - SAFE_CLOUD_SENSITIVITY))
                    )
                if external_policy != "approval_required":
                    self.error(f"profile {profile_id}: cloud_api_llm external_send_policy must be approval_required")
                if approval.get("external_send") != "approver_required":
                    self.error(f"profile {profile_id}: cloud_api_llm approval_policy.external_send must be approver_required")
                if boundary.get("redaction_required") is not True:
                    self.error(f"profile {profile_id}: cloud_api_llm redaction_required must be true")
            elif provider_class == "upper_agent_wrapper":
                if approval.get("tool_write") != "blocked":
                    self.error(f"profile {profile_id}: upper_agent_wrapper tool_write must be blocked")
                if external_policy != "deny":
                    self.error(f"profile {profile_id}: upper_agent_wrapper external_send_policy must be deny")
            elif provider_class == "deterministic_fallback":
                if approval.get("budget_override") != "blocked":
                    self.error(f"profile {profile_id}: deterministic_fallback budget_override must be blocked")

    def validate_provider_class_match(self, profile_id: str, provider_class: str, provider: dict[str, Any]) -> None:
        provider_type = str(provider.get("type") or "").strip()
        if provider_class == "local_llm" and provider_type not in LOCAL_PROVIDER_TYPES:
            self.error(f"profile {profile_id}: local_llm provider must use local provider type, got {provider_type}")
        if provider_class == "cloud_api_llm" and provider_type not in CLOUD_PROVIDER_TYPES:
            self.error(f"profile {profile_id}: cloud_api_llm provider must use api/cloud provider type, got {provider_type}")
        if provider_class == "upper_agent_wrapper" and provider_type not in UPPER_PROVIDER_TYPES:
            self.warn(f"profile {profile_id}: upper_agent_wrapper provider type is not explicit in model registry")
        if provider_class == "deterministic_fallback" and provider_type not in FALLBACK_PROVIDER_TYPES:
            self.warn(f"profile {profile_id}: deterministic_fallback provider type is not explicit in model registry")

    def validate_jobs(
        self,
        jobs: dict[str, dict[str, Any]],
        profiles: dict[str, dict[str, Any]],
        packs: dict[str, dict[str, Any]],
    ) -> None:
        for template_id, template in jobs.items():
            submit = dict(template.get("submit_contract") or {})
            if submit.get("surface") != "agent.submit":
                self.error(f"job {template_id}: submit_contract.surface must be agent.submit")
            for key in ("status_surface", "events_surface", "report_surface"):
                if not str(submit.get(key) or "").startswith("agent."):
                    self.error(f"job {template_id}: submit_contract.{key} must use agent.* surface")

            schema = dict(template.get("input_schema") or {})
            required = self.string_set(schema.get("required_fields"))
            sensitivity_field = str(schema.get("sensitivity_field") or "sensitivity")
            if sensitivity_field not in required:
                self.error(f"job {template_id}: required_fields must include sensitivity field {sensitivity_field}")
            if schema.get("freeform_context_allowed") is not False:
                self.error(f"job {template_id}: freeform_context_allowed must be false unless separately reviewed")

            allowed_profiles = self.string_set(template.get("allowed_profile_ids"))
            required_packs = self.string_set(template.get("required_capability_packs"))
            if not allowed_profiles:
                self.error(f"job {template_id}: allowed_profile_ids must not be empty")
            if not required_packs:
                self.error(f"job {template_id}: required_capability_packs must not be empty")
            if "*" in required_packs:
                self.error(f"job {template_id}: required_capability_packs must not contain wildcard")

            provider_policy = dict(template.get("provider_policy") or {})
            default_profile_id = str(provider_policy.get("default_profile_id") or "").strip()
            if default_profile_id and default_profile_id not in allowed_profiles:
                self.error(f"job {template_id}: default_profile_id must be allowed by template")
            allowed_provider_classes = self.string_set(provider_policy.get("allowed_provider_classes"))
            for profile_id in allowed_profiles:
                profile = profiles.get(profile_id)
                if profile is None:
                    self.error(f"job {template_id}: unknown allowed profile {profile_id}")
                    continue
                if template_id not in self.string_set(profile.get("allowed_job_templates")):
                    self.error(f"job {template_id}: profile {profile_id} does not reciprocally allow template")
                provider_class = str(profile.get("provider_class") or "")
                if allowed_provider_classes and provider_class not in allowed_provider_classes:
                    self.error(f"job {template_id}: provider class {provider_class} not allowed by provider_policy")
                for pack_id in required_packs:
                    if pack_id not in self.string_set(profile.get("allowed_capability_packs")):
                        self.error(f"job {template_id}: profile {profile_id} does not allow required pack {pack_id}")

            for pack_id in required_packs:
                pack = packs.get(pack_id)
                if pack is None:
                    self.error(f"job {template_id}: unknown required capability pack {pack_id}")
                    continue
                if template_id not in self.string_set(pack.get("allowed_template_ids")):
                    self.error(f"job {template_id}: pack {pack_id} does not reciprocally allow template")

            schedule = dict(template.get("schedule_trigger") or {})
            supported = self.string_set(schedule.get("supported_triggers"))
            if supported & {"cron", "launchd", "ci", "external_agent"}:
                idempotency_fields = self.string_set(schedule.get("idempotency_key_fields"))
                if "template_id" not in idempotency_fields:
                    self.error(f"job {template_id}: scheduled jobs must include template_id in idempotency_key_fields")
                if len(idempotency_fields) < 2:
                    self.error(f"job {template_id}: scheduled jobs need at least one business idempotency field")
                policy_raw = schedule.get("idempotency_key_policy")
                if not isinstance(policy_raw, dict):
                    self.error(f"job {template_id}: scheduled jobs must define idempotency_key_policy")
                    policy: dict[str, Any] = {}
                else:
                    policy = dict(policy_raw)
                key_format = str(policy.get("format") or "").strip()
                if not key_format:
                    self.error(f"job {template_id}: scheduled jobs must define idempotency_key_policy.format")
                else:
                    placeholders = {item.strip() for item in re.findall(r"\{([^{}]+)\}", key_format) if item.strip()}
                    if placeholders != idempotency_fields:
                        self.error(
                            f"job {template_id}: idempotency_key_policy.format placeholders must match idempotency_key_fields"
                        )
                    if not key_format.startswith("stage12:"):
                        self.error(f"job {template_id}: idempotency_key_policy.format must start with stage12:")
                examples = policy.get("examples")
                if not isinstance(examples, list) or not examples:
                    self.error(f"job {template_id}: idempotency_key_policy.examples must not be empty")
                else:
                    for example in examples:
                        normalized = str(example or "").strip()
                        if not normalized:
                            self.error(f"job {template_id}: idempotency_key_policy.examples cannot include blank values")
                            continue
                        if "{" in normalized or "}" in normalized:
                            self.error(f"job {template_id}: idempotency_key_policy.examples must be concrete keys")
                        if not normalized.startswith("stage12:"):
                            self.error(f"job {template_id}: idempotency_key_policy.examples must start with stage12:")
                duplicate_policy = str(policy.get("recommended_duplicate_policy") or "").strip()
                if duplicate_policy not in {"run", "skip", "fail"}:
                    self.error(
                        f"job {template_id}: idempotency_key_policy.recommended_duplicate_policy must be run, skip, or fail"
                    )

    def validate_packs(
        self,
        packs: dict[str, dict[str, Any]],
        profiles: dict[str, dict[str, Any]],
        jobs: dict[str, dict[str, Any]],
    ) -> None:
        for pack_id, pack in packs.items():
            allowed_tools = self.string_set(pack.get("allowed_tool_ids"))
            denied_tools = self.string_set(pack.get("denied_tool_ids"))
            runtime_surfaces = self.string_set(pack.get("runtime_read_surfaces"))
            if "*" in allowed_tools or "*" in denied_tools:
                self.error(f"pack {pack_id}: wildcard tool ids are not allowed")
            if allowed_tools & denied_tools:
                self.error(f"pack {pack_id}: tools cannot be both allowed and denied: {sorted(allowed_tools & denied_tools)}")
            if not allowed_tools and not runtime_surfaces:
                self.error(f"pack {pack_id}: must define allowed tools or runtime read surfaces")

            approval = dict(pack.get("approval_requirements") or {})
            if approval.get("tool_write") not in {"blocked", "approver_required"}:
                self.error(f"pack {pack_id}: tool_write must be blocked or approver_required")
            if approval.get("external_send") not in {"blocked", "approval_required", "approver_required"}:
                self.error(f"pack {pack_id}: external_send must be blocked or approval/approver required")
            if approval.get("pack_change") != "admin_required":
                self.error(f"pack {pack_id}: pack_change must be admin_required")

            boundary = dict(pack.get("data_boundary") or {})
            boundary_policy = str(boundary.get("external_send_policy") or "")
            if boundary_policy not in {"deny", "approval_required", "approver_required"}:
                self.error(f"pack {pack_id}: data_boundary.external_send_policy is invalid")

            allowed_profiles = self.string_set(pack.get("allowed_profile_ids"))
            allowed_templates = self.string_set(pack.get("allowed_template_ids"))
            for profile_id in allowed_profiles:
                profile = profiles.get(profile_id)
                if profile is None:
                    self.error(f"pack {pack_id}: unknown allowed profile {profile_id}")
                    continue
                if pack_id not in self.string_set(profile.get("allowed_capability_packs")):
                    self.error(f"pack {pack_id}: profile {profile_id} does not reciprocally allow pack")
                provider_class = str(profile.get("provider_class") or "")
                if provider_class == "local_llm" and boundary_policy not in {"deny", "approval_required", "approver_required"}:
                    self.error(f"pack {pack_id}: local profile {profile_id} requires controlled external send policy")
                if provider_class == "cloud_api_llm":
                    allowed_sensitivity = self.string_set(boundary.get("allowed_sensitivity"))
                    if allowed_sensitivity - (SAFE_CLOUD_SENSITIVITY | {"internal"}):
                        self.error(f"pack {pack_id}: cloud profile {profile_id} exposes unsafe sensitivity")
            for template_id in allowed_templates:
                template = jobs.get(template_id)
                if template is None:
                    self.error(f"pack {pack_id}: unknown allowed template {template_id}")
                    continue
                if pack_id not in self.string_set(template.get("required_capability_packs")):
                    self.warn(f"pack {pack_id}: template {template_id} does not currently require pack")

    def validate_provider_routes(self, model_doc: dict[str, Any], providers: dict[str, dict[str, Any]]) -> None:
        rules = model_doc.get("routing_rules")
        if not isinstance(rules, list):
            self.error("model_registry: routing_rules must be a list")
            return
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                self.error(f"model_registry: routing rule {index} must be object")
                continue
            provider_id = str(rule.get("use_provider") or "").strip()
            if provider_id and provider_id not in providers:
                self.error(f"model_registry: routing rule {index} uses unknown provider {provider_id}")
            if bool(rule.get("require_human_approval")) and provider_id:
                self.warn(f"model_registry: routing rule {index} has approval and direct provider; verify intent")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Stage 12 LLM harness policy registries.")
    parser.add_argument("--agent-profiles", type=Path, default=DEFAULT_AGENT_PROFILES)
    parser.add_argument("--job-templates", type=Path, default=DEFAULT_JOB_TEMPLATES)
    parser.add_argument("--capability-packs", type=Path, default=DEFAULT_CAPABILITY_PACKS)
    parser.add_argument("--model-registry", type=Path, default=DEFAULT_MODEL_REGISTRY)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict-warnings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validator = HarnessValidator(
        profiles_path=args.agent_profiles,
        jobs_path=args.job_templates,
        packs_path=args.capability_packs,
        model_registry_path=args.model_registry,
    )
    payload = validator.validate()
    if args.strict_warnings and payload["warnings"]:
        payload["status"] = "FAIL"

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Stage 12 LLM harness validation: {payload['status']}")
        counts = payload["counts"]
        print(
            "counts: "
            f"profiles={counts['profiles']} "
            f"job_templates={counts['job_templates']} "
            f"capability_packs={counts['capability_packs']} "
            f"model_providers={counts['model_providers']} "
            f"errors={counts['errors']} "
            f"warnings={counts['warnings']}"
        )
        for error in payload["errors"]:
            print(f"[ERROR] {error}")
        for warning in payload["warnings"]:
            print(f"[WARN] {warning}")

    if payload["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
