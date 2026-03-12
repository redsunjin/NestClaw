from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.auth import ActorContext, VALID_ROLES
from app.tool_registry import ToolRegistry, ToolRegistryError, get_tool_capability, list_tool_capabilities


@dataclass
class ToolCatalogServiceDeps:
    registry: ToolRegistry
    authorize: Callable[..., str]
    error: Callable[..., None]


class ToolCatalogService:
    def __init__(self, deps: ToolCatalogServiceDeps) -> None:
        self.deps = deps

    def list_tools(
        self,
        capability_family: str | None,
        external_system: str | None,
        actor: ActorContext,
    ) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, set(VALID_ROLES), "list_tools")
        items = [
            item.as_dict()
            for item in list_tool_capabilities(
                self.deps.registry,
                capability_family=capability_family,
                external_system=external_system,
            )
        ]
        return {"items": items, "count": len(items)}

    def get_tool(self, tool_id: str, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, set(VALID_ROLES), "get_tool")
        try:
            return get_tool_capability(self.deps.registry, tool_id).as_dict()
        except ToolRegistryError as exc:
            self.deps.error(404, "TOOL_NOT_FOUND", str(exc))
            raise AssertionError("unreachable")
