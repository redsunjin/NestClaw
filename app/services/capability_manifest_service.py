from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from app.auth import ActorContext, VALID_ROLES
from app.runtime_taxonomy import readiness_state_summary
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
            "stage8_live_readiness": readiness_state_summary(missing)
        }

    def get_manifest(self, actor: ActorContext) -> dict[str, Any]:
        self.deps.authorize(actor.actor_role, set(VALID_ROLES), "capability_manifest")
        tools = [item.as_dict() for item in list_tool_capabilities(self.deps.registry)]
        return {
            "manifest_version": "2026-04-04",
            "product_posture": "orchestration_backend_with_human_dashboard",
            "primary_entrypoint": "job.list/describe/run + agent.submit/status/events",
            "workflow_families": [
                {
                    "kind": "task",
                    "status": "ai_first_baseline",
                    "notes": "llm planner baseline with summary/ticket/slack scope",
                },
                {
                    "kind": "incident",
                    "status": "ai_planner_with_deterministic_fallback",
                    "notes": "provider-backed incident planning baseline with deterministic fallback and dry-run execution",
                },
            ],
            "delivery_surfaces": [
                {"surface": "http", "status": "stable_baseline"},
                {"surface": "cli", "status": "stable_baseline"},
                {"surface": "mcp", "status": "stable_baseline"},
                {"surface": "web_quickstart", "status": "lightweight"},
                {"surface": "web_console", "status": "operator_dashboard"},
            ],
            "transport": {
                "mcp": {
                    "baseline": "stdio",
                    "status": "stable_baseline",
                    "remote_gateway": "future_boundary",
                    "actor_context_required": True,
                }
            },
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
                    "agent.bundle",
                    "agent.handoff",
                    "job.list",
                    "job.describe",
                    "job.run",
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
                "incident ai planner remains constrained to the current ticket/slack tool set",
                "live external readiness can be blocked by missing env",
            ],
        }
