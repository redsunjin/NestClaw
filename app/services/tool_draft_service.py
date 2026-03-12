from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping
from uuid import uuid4

from app.auth import ActorContext, VALID_ROLES


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", ".", lowered)
    lowered = re.sub(r"\.+", ".", lowered)
    return lowered.strip(".") or "custom"


@dataclass
class ToolDraftServiceDeps:
    authorize: Callable[..., str]
    error: Callable[..., None]
    now_iso: Callable[[], str]
    drafts_root: Path


class ToolDraftService:
    def __init__(self, deps: ToolDraftServiceDeps) -> None:
        self.deps = deps
        self.deps.drafts_root.mkdir(parents=True, exist_ok=True)

    def _field(self, req: Any, name: str, default: Any = None) -> Any:
        if isinstance(req, Mapping):
            return req.get(name, default)
        return getattr(req, name, default)

    def _coerce_fields(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [part.strip() for part in str(value).split(",") if part.strip()]

    def _guess_external_system(self, request_text: str) -> str:
        text = request_text.lower()
        if "slack" in text:
            return "slack"
        if "redmine" in text:
            return "redmine"
        return "internal"

    def _guess_capability_family(self, request_text: str) -> str:
        text = request_text.lower()
        if any(token in text for token in ("message", "notify", "notification", "slack", "chat")):
            return "messaging"
        if "ticket" in text:
            return "ticketing"
        return "general"

    def _default_adapter(self, external_system: str) -> str:
        if external_system == "slack":
            return "slack_api"
        if external_system == "redmine":
            return "redmine_mcp"
        return "provider_invoker"

    def _default_method(self, external_system: str, capability_family: str) -> str:
        if external_system == "slack" or capability_family == "messaging":
            return "message.send"
        if external_system == "redmine":
            return "issue.create"
        return "summary.generate"

    def _default_fields(self, external_system: str, capability_family: str) -> list[str]:
        if external_system == "slack" or capability_family == "messaging":
            return ["channel", "text"]
        if external_system == "redmine":
            return ["project_id", "subject", "description"]
        return ["input"]

    def _render_yaml(self, draft_id: str, created_by: str, request_text: str, spec: dict[str, Any]) -> str:
        lines = [
            f'draft_id: "{draft_id}"',
            'status: "DRAFT_REVIEW_REQUIRED"',
            f'created_at: "{self.deps.now_iso()}"',
            f'created_by: "{created_by}"',
        ]
        if request_text:
            lines.append(f"request_text: {json.dumps(request_text, ensure_ascii=False)}")
        lines.extend(
            [
                "tool:",
                f'  id: "{spec["tool_id"]}"',
                f"  title: {json.dumps(spec['title'], ensure_ascii=False)}",
                f"  description: {json.dumps(spec['description'], ensure_ascii=False)}",
                f'  adapter: "{spec["adapter"]}"',
                f'  method: "{spec["method"]}"',
                f'  action_type: "{spec["action_type"]}"',
                f'  external_system: "{spec["external_system"]}"',
                f'  capability_family: "{spec["capability_family"]}"',
                f'  default_risk_level: "{spec["default_risk_level"]}"',
                f'  default_approval_required: {"true" if spec["default_approval_required"] else "false"}',
                f'  supports_dry_run: {"true" if spec["supports_dry_run"] else "false"}',
                "  required_payload_fields:",
            ]
        )
        for field_name in spec["required_payload_fields"]:
            lines.append(f'    - "{field_name}"')
        return "\n".join(lines) + "\n"

    def create_draft(self, req: Any, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, set(VALID_ROLES), "create_tool_draft")
        request_text = str(self._field(req, "request_text", "") or "").strip()
        external_system = str(self._field(req, "external_system", "") or "").strip().lower() or self._guess_external_system(request_text)
        capability_family = (
            str(self._field(req, "capability_family", "") or "").strip().lower()
            or self._guess_capability_family(request_text)
        )
        title = str(self._field(req, "title", "") or "").strip() or request_text or f"{external_system} {capability_family} tool"
        tool_id = str(self._field(req, "tool_id", "") or "").strip() or f"{external_system}.{capability_family}.{_slug(title)}"
        adapter = str(self._field(req, "adapter", "") or "").strip() or self._default_adapter(external_system)
        method = str(self._field(req, "method", "") or "").strip() or self._default_method(external_system, capability_family)
        action_type = str(self._field(req, "action_type", "") or "").strip() or tool_id.replace(".", "_")
        description = str(self._field(req, "description", "") or "").strip() or f"{title} through {adapter}."
        required_payload_fields = self._coerce_fields(self._field(req, "required_payload_fields")) or self._default_fields(
            external_system,
            capability_family,
        )
        if not tool_id or not title:
            self.deps.error(400, "INVALID_REQUEST", "tool_id and title could not be derived")

        raw_default_approval_required = self._field(req, "default_approval_required", True)
        raw_supports_dry_run = self._field(req, "supports_dry_run", True)

        spec = {
            "tool_id": tool_id,
            "title": title,
            "description": description,
            "adapter": adapter,
            "method": method,
            "action_type": action_type,
            "external_system": external_system or "internal",
            "capability_family": capability_family or "general",
            "default_risk_level": str(self._field(req, "default_risk_level", "medium") or "medium"),
            "default_approval_required": True if raw_default_approval_required is None else bool(raw_default_approval_required),
            "supports_dry_run": True if raw_supports_dry_run is None else bool(raw_supports_dry_run),
            "required_payload_fields": required_payload_fields,
        }
        draft_id = f"tooldraft_{uuid4().hex[:10]}"
        path = self.deps.drafts_root / f"{draft_id}.yaml"
        content = self._render_yaml(draft_id, actor.actor_id, request_text, spec)
        path.write_text(content, encoding="utf-8")
        return {
            "draft_id": draft_id,
            "status": "DRAFT_REVIEW_REQUIRED",
            "path": str(path),
            "tool": spec,
            "content": content,
        }

    def get_draft(self, draft_id: str, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, set(VALID_ROLES), "get_tool_draft")
        normalized = str(draft_id or "").strip()
        if not normalized:
            self.deps.error(400, "INVALID_REQUEST", "draft_id is required")
        path = self.deps.drafts_root / f"{normalized}.yaml"
        if not path.is_file():
            self.deps.error(404, "TOOL_DRAFT_NOT_FOUND", f"tool draft not found: {draft_id}")
        return {
            "draft_id": normalized,
            "path": str(path),
            "content": path.read_text(encoding="utf-8"),
        }
