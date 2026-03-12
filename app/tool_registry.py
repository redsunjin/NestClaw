from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TOOL_REGISTRY_PATH = Path("configs/tool_registry.yaml")


class ToolRegistryError(RuntimeError):
    """Raised when the tool registry file is missing or invalid."""


@dataclass(frozen=True)
class ToolCapability:
    tool_id: str
    title: str
    description: str
    adapter: str
    method: str
    action_type: str
    external_system: str
    capability_family: str
    default_risk_level: str
    default_approval_required: bool
    supports_dry_run: bool
    required_payload_fields: tuple[str, ...]

    def input_schema(self) -> dict[str, Any]:
        properties = {field_name: {"type": "string"} for field_name in self.required_payload_fields}
        return {
            "type": "object",
            "properties": properties,
            "required": list(self.required_payload_fields),
            "additionalProperties": True,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "title": self.title,
            "description": self.description,
            "adapter": self.adapter,
            "method": self.method,
            "action_type": self.action_type,
            "external_system": self.external_system,
            "capability_family": self.capability_family,
            "default_risk_level": self.default_risk_level,
            "default_approval_required": self.default_approval_required,
            "supports_dry_run": self.supports_dry_run,
            "required_payload_fields": list(self.required_payload_fields),
            "input_schema": self.input_schema(),
        }


@dataclass(frozen=True)
class ToolRegistry:
    version: int
    tools: tuple[ToolCapability, ...]


_CACHE: dict[str, tuple[int, ToolRegistry]] = {}


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
        raise ToolRegistryError(f"invalid yaml line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def _parse_list_of_maps(lines: list[str], index: int, item_indent: int) -> tuple[list[dict[str, Any]], int]:
    items: list[dict[str, Any]] = []
    while index < len(lines):
        line = lines[index]
        indent = _indent(line)
        stripped = line.strip()
        if indent < item_indent:
            break
        if indent != item_indent or not stripped.startswith("- "):
            raise ToolRegistryError(f"invalid list item: {stripped}")

        item: dict[str, Any] = {}
        remainder = stripped[2:].strip()
        if remainder:
            key, value = _parse_key_value(remainder)
            item[key] = _parse_scalar(value)
        index += 1

        while index < len(lines):
            next_line = lines[index]
            next_indent = _indent(next_line)
            if next_indent <= item_indent:
                break
            if next_indent != item_indent + 2:
                raise ToolRegistryError(f"unexpected indentation in list item: {next_line.strip()}")
            key, value = _parse_key_value(next_line.strip())
            item[key] = _parse_scalar(value)
            index += 1
        items.append(item)
    return items, index


def _logical_lines(path: Path) -> list[str]:
    if not path.is_file():
        raise ToolRegistryError(f"tool registry file not found: {path}")
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(raw_line.rstrip())
    return lines


def _parse_required_fields(value: Any) -> tuple[str, ...]:
    raw = str(value or "").strip()
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _load_registry_from_path(path: Path) -> ToolRegistry:
    lines = _logical_lines(path)
    version = 1
    tools_raw: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _indent(line) != 0:
            raise ToolRegistryError(f"unexpected top-level indentation: {line.strip()}")
        key, value = _parse_key_value(line.strip())
        if key == "version":
            version = int(_parse_scalar(value))
            index += 1
            continue
        if key == "tools":
            tools_raw, index = _parse_list_of_maps(lines, index + 1, 2)
            continue
        raise ToolRegistryError(f"unsupported top-level key: {key}")

    tools = tuple(
        ToolCapability(
            tool_id=str(item.get("id") or "").strip(),
            title=str(item.get("title") or "").strip(),
            description=str(item.get("description") or "").strip(),
            adapter=str(item.get("adapter") or "").strip(),
            method=str(item.get("method") or "").strip(),
            action_type=str(item.get("action_type") or "").strip(),
            external_system=str(item.get("external_system") or "").strip(),
            capability_family=str(item.get("capability_family") or "").strip(),
            default_risk_level=str(item.get("default_risk_level") or "medium").strip() or "medium",
            default_approval_required=bool(item.get("default_approval_required", False)),
            supports_dry_run=bool(item.get("supports_dry_run", False)),
            required_payload_fields=_parse_required_fields(item.get("required_payload_fields")),
        )
        for item in tools_raw
    )
    if not tools:
        raise ToolRegistryError("tool registry has no tools")
    if any(not tool.tool_id for tool in tools):
        raise ToolRegistryError("tool id is required")
    return ToolRegistry(version=version, tools=tools)


def load_tool_registry(path: str | Path = DEFAULT_TOOL_REGISTRY_PATH) -> ToolRegistry:
    target = Path(path)
    stat = target.stat()
    cache_key = str(target.resolve())
    cached = _CACHE.get(cache_key)
    if cached and cached[0] == stat.st_mtime_ns:
        return cached[1]
    registry = _load_registry_from_path(target)
    _CACHE[cache_key] = (stat.st_mtime_ns, registry)
    return registry


def list_tool_capabilities(
    registry: ToolRegistry,
    *,
    capability_family: str | None = None,
    external_system: str | None = None,
) -> tuple[ToolCapability, ...]:
    items = registry.tools
    if capability_family:
        normalized_family = capability_family.strip().lower()
        items = tuple(item for item in items if item.capability_family.lower() == normalized_family)
    if external_system:
        normalized_system = external_system.strip().lower()
        items = tuple(item for item in items if item.external_system.lower() == normalized_system)
    return items


def get_tool_capability(registry: ToolRegistry, tool_id: str) -> ToolCapability:
    normalized_tool_id = tool_id.strip()
    for item in registry.tools:
        if item.tool_id == normalized_tool_id:
            return item
    raise ToolRegistryError(f"tool capability not found: {tool_id}")
