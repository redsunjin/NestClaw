from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL_REGISTRY_PATH = Path("configs/model_registry.yaml")


class ModelRegistryError(RuntimeError):
    """Raised when the model registry file is missing or invalid."""


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    provider_type: str
    enabled: bool
    engine: str
    model: str
    purpose: str


@dataclass(frozen=True)
class RoutingRule:
    when: dict[str, Any]
    use_provider: str | None = None
    require_human_approval: bool = False


@dataclass(frozen=True)
class ModelRegistry:
    version: int
    providers: tuple[ProviderConfig, ...]
    routing_rules: tuple[RoutingRule, ...]


@dataclass(frozen=True)
class ProviderSelection:
    provider_id: str | None
    provider_type: str | None
    engine: str | None
    model: str | None
    purpose: str | None
    selection_source: str
    matched_rule_index: int | None
    sensitivity: str
    task_type: str
    external_send: bool
    requires_human_approval: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "engine": self.engine,
            "model": self.model,
            "purpose": self.purpose,
            "selection_source": self.selection_source,
            "matched_rule_index": self.matched_rule_index,
            "sensitivity": self.sensitivity,
            "task_type": self.task_type,
            "external_send": self.external_send,
            "requires_human_approval": self.requires_human_approval,
        }


_CACHE: dict[str, tuple[int, ModelRegistry]] = {}


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if text.isdigit():
        return int(text)
    return text


def _parse_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ModelRegistryError(f"invalid yaml line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def _parse_nested_map(lines: list[str], index: int, expected_indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line = lines[index]
        indent = _indent(line)
        if indent < expected_indent:
            break
        if indent != expected_indent:
            raise ModelRegistryError(f"unexpected indentation: {line.strip()}")
        key, value = _parse_key_value(line.strip())
        if value:
            result[key] = _parse_scalar(value)
            index += 1
            continue
        nested, index = _parse_nested_map(lines, index + 1, expected_indent + 2)
        result[key] = nested
    return result, index


def _parse_list_of_maps(lines: list[str], index: int, item_indent: int) -> tuple[list[dict[str, Any]], int]:
    items: list[dict[str, Any]] = []
    while index < len(lines):
        line = lines[index]
        indent = _indent(line)
        stripped = line.strip()
        if indent < item_indent:
            break
        if indent != item_indent or not stripped.startswith("- "):
            raise ModelRegistryError(f"invalid list item: {stripped}")

        item: dict[str, Any] = {}
        remainder = stripped[2:].strip()
        if remainder:
            key, value = _parse_key_value(remainder)
            if value:
                item[key] = _parse_scalar(value)
                index += 1
            else:
                nested, index = _parse_nested_map(lines, index + 1, item_indent + 4)
                item[key] = nested
        else:
            index += 1

        while index < len(lines):
            next_line = lines[index]
            next_indent = _indent(next_line)
            if next_indent <= item_indent:
                break
            if next_indent != item_indent + 2:
                raise ModelRegistryError(f"unexpected indentation in list item: {next_line.strip()}")
            key, value = _parse_key_value(next_line.strip())
            if value:
                item[key] = _parse_scalar(value)
                index += 1
                continue
            nested, index = _parse_nested_map(lines, index + 1, item_indent + 4)
            item[key] = nested
        items.append(item)
    return items, index


def _logical_lines(path: Path) -> list[str]:
    if not path.is_file():
        raise ModelRegistryError(f"model registry file not found: {path}")
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(raw_line.rstrip())
    return lines


def _load_registry_from_path(path: Path) -> ModelRegistry:
    lines = _logical_lines(path)
    version = 1
    providers_raw: list[dict[str, Any]] = []
    rules_raw: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _indent(line) != 0:
            raise ModelRegistryError(f"unexpected top-level indentation: {line.strip()}")
        key, value = _parse_key_value(line.strip())
        if key == "version":
            version = int(_parse_scalar(value))
            index += 1
            continue
        if key == "providers":
            providers_raw, index = _parse_list_of_maps(lines, index + 1, 2)
            continue
        if key == "routing_rules":
            rules_raw, index = _parse_list_of_maps(lines, index + 1, 2)
            continue
        raise ModelRegistryError(f"unsupported top-level key: {key}")

    providers = tuple(
        ProviderConfig(
            provider_id=str(item.get("id") or "").strip(),
            provider_type=str(item.get("type") or "").strip(),
            enabled=bool(item.get("enabled", False)),
            engine=str(item.get("engine") or "").strip(),
            model=str(item.get("model") or "").strip(),
            purpose=str(item.get("purpose") or "").strip(),
        )
        for item in providers_raw
    )
    if not providers:
        raise ModelRegistryError("model registry has no providers")
    if any(not provider.provider_id for provider in providers):
        raise ModelRegistryError("provider id is required")

    routing_rules = tuple(
        RoutingRule(
            when=dict(item.get("when") or {}),
            use_provider=str(item.get("use_provider") or "").strip() or None,
            require_human_approval=bool(item.get("require_human_approval", False)),
        )
        for item in rules_raw
    )
    return ModelRegistry(version=version, providers=providers, routing_rules=routing_rules)


def load_model_registry(path: str | Path = DEFAULT_MODEL_REGISTRY_PATH) -> ModelRegistry:
    target = Path(path)
    stat = target.stat()
    cache_key = str(target.resolve())
    cached = _CACHE.get(cache_key)
    if cached and cached[0] == stat.st_mtime_ns:
        return cached[1]
    registry = _load_registry_from_path(target)
    _CACHE[cache_key] = (stat.st_mtime_ns, registry)
    return registry


def select_provider(
    registry: ModelRegistry,
    *,
    sensitivity: str,
    task_type: str,
    external_send: bool = False,
) -> ProviderSelection:
    context = {
        "sensitivity": str(sensitivity or "").strip().lower() or "low",
        "task_type": str(task_type or "").strip().lower() or "general",
        "external_send": bool(external_send),
    }
    providers = {provider.provider_id: provider for provider in registry.providers if provider.enabled}
    selected_provider: ProviderConfig | None = None
    matched_rule_index: int | None = None
    requires_human_approval = False
    selection_source = "default_enabled_provider"

    for index, rule in enumerate(registry.routing_rules):
        if not all(context.get(key) == value for key, value in rule.when.items()):
            continue
        if rule.require_human_approval:
            requires_human_approval = True
        if selected_provider is None and rule.use_provider:
            selected_provider = providers.get(rule.use_provider)
            if selected_provider is None:
                raise ModelRegistryError(f"routing rule references unknown or disabled provider: {rule.use_provider}")
            matched_rule_index = index
            selection_source = "routing_rule"

    if selected_provider is None:
        selected_provider = next(iter(providers.values()), None)

    return ProviderSelection(
        provider_id=selected_provider.provider_id if selected_provider else None,
        provider_type=selected_provider.provider_type if selected_provider else None,
        engine=selected_provider.engine if selected_provider else None,
        model=selected_provider.model if selected_provider else None,
        purpose=selected_provider.purpose if selected_provider else None,
        selection_source=selection_source if selected_provider else "no_provider_available",
        matched_rule_index=matched_rule_index,
        sensitivity=context["sensitivity"],
        task_type=context["task_type"],
        external_send=context["external_send"],
        requires_human_approval=requires_human_approval,
    )
