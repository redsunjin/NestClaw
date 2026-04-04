from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from app.auth import ActorContext, VALID_ROLES
from app.tool_registry import ToolRegistry, list_tool_capabilities


STAGE8_REQUIRED_ENVS = (
    "NEWCLAW_STAGE8_SANDBOX_ENABLED",
    "NEWCLAW_STAGE8_SANDBOX_BASE_URL",
    "NEWCLAW_STAGE8_SANDBOX_PROJECT",
    "NEWCLAW_STAGE8_LIVE_ENABLED",
    "NEWCLAW_REDMINE_MCP_ENDPOINT",
)


@dataclass
class CapabilityManifestServiceDeps:
    registry: ToolRegistry
    authorize: Callable[..., str]


class CapabilityManifestService:
    def __init__(self, deps: CapabilityManifestServiceDeps) -> None:
        self.deps = deps

    def _readiness(self) -> dict[str, Any]:
        missing = [name for name in STAGE8_REQUIRED_ENVS if not os.getenv(name, "").strip()]
        return {
            "stage8_live_readiness": {
                "status": "ready" if not missing else "blocked",
                "missing_env": missing,
            }
        }

    def get_manifest(self, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, set(VALID_ROLES), "capability_manifest")
        tools = [item.as_dict() for item in list_tool_capabilities(self.deps.registry)]
        return {
            "manifest_version": "2026-04-04",
            "product_posture": "orchestration_backend_with_human_dashboard",
            "primary_entrypoint": "agent.submit/status/events",
            "workflow_families": [
                {
                    "kind": "task",
                    "status": "ai_first_baseline",
                    "notes": "llm planner baseline with summary/ticket/slack scope",
                },
                {
                    "kind": "incident",
                    "status": "common_contract_deterministic_planner",
                    "notes": "shared planner/executor contract with dry-run centered planning",
                },
            ],
            "delivery_surfaces": [
                {"surface": "http", "status": "stable_baseline"},
                {"surface": "cli", "status": "stable_baseline"},
                {"surface": "mcp", "status": "stable_baseline"},
                {"surface": "web_quickstart", "status": "lightweight"},
                {"surface": "web_console", "status": "operator_dashboard"},
            ],
            "roles": sorted(VALID_ROLES),
            "auth_modes": [
                "jwt_local",
                "jwt_idp",
                "trusted_sso_headers",
                "compat_actor_headers",
            ],
            "controls": {
                "safe_for_upper_agents": [
                    "agent.submit",
                    "agent.status",
                    "agent.events",
                    "agent.recent",
                    "agent.report",
                    "approval.get",
                    "catalog.list",
                    "catalog.get",
                    "catalog.create_draft",
                    "catalog.get_draft",
                    "catalog.validate_draft",
                    "catalog.manifest",
                ],
                "human_or_elevated_only": [
                    "approval.approve",
                    "approval.reject",
                    "catalog.apply_draft",
                    "catalog.rollback_tool",
                    "live_execution",
                ],
            },
            "tool_catalog": {
                "count": len(tools),
                "items": tools,
            },
            "readiness": self._readiness(),
            "known_limits": [
                "broader multi-step planning is still limited",
                "incident ai planner is not the default runtime path yet",
                "live external readiness can be blocked by missing env",
            ],
        }
