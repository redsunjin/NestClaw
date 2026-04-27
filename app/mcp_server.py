from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

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
from app.stage12_jobs import job_describe_payload, job_list_payload, run_stage12_job


SERVER_NAME = "newclaw-mcp"
SERVER_VERSION = "0.1.0"
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
JSONRPC_VERSION = "2.0"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


def _error_payload(code: str, message: str, *, status_code: int = 1) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "status_code": status_code}}


def _coerce_http_error(exc: HTTPException) -> dict[str, Any]:
    if isinstance(exc.detail, dict):
        return exc.detail
    return _error_payload("HTTP_ERROR", str(exc.detail), status_code=exc.status_code)


def _actor_context(actor_id: str, actor_role: str, *, source: str = "mcp") -> ActorContext:
    normalized_role = actor_role.strip().lower()
    if normalized_role not in VALID_ROLES:
        raise ValueError(f"unsupported actor_role: {actor_role}")
    normalized_actor_id = actor_id.strip()
    if not normalized_actor_id:
        raise ValueError("actor_id is required")
    return ActorContext(actor_id=normalized_actor_id, actor_role=normalized_role, source=source)


def _invoke(callable_obj: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return callable_obj(*args, **kwargs)
    except HTTPException as exc:
        return _coerce_http_error(exc)
    except ValueError as exc:
        return _error_payload("INVALID_REQUEST", str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        return _error_payload("MCP_SERVER_ERROR", str(exc))


class NewClawMcpServer:
    def __init__(self) -> None:
        self.orchestration_service = build_orchestration_service(sync_execution=True)
        self.approval_service = build_approval_service(sync_execution=True)
        self.tool_catalog_service = build_tool_catalog_service()
        self.capability_manifest_service = build_capability_manifest_service()
        self.tool_draft_service = build_tool_draft_service()
        self.initialized = False
        self.tools = self._build_tools()

    def _build_tools(self) -> dict[str, ToolSpec]:
        return {
            "agent.submit": ToolSpec(
                name="agent.submit",
                title="Submit Agent Request",
                description="Create and optionally run an agent workflow request.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "request_text": {"type": "string"},
                        "requested_by": {"type": "string"},
                        "task_kind": {"type": "string", "enum": ["auto", "task", "incident"]},
                        "title": {"type": "string"},
                        "metadata": {"type": "object"},
                        "auto_run": {"type": "boolean"},
                        "incident_run_mode": {"type": "string", "enum": ["dry-run", "mcp-live", "live"]},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["request_text", "requested_by"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_submit,
            ),
            "agent.status": ToolSpec(
                name="agent.status",
                title="Get Agent Status",
                description="Fetch the current task status for an agent workflow.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["task_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_status,
            ),
            "agent.events": ToolSpec(
                name="agent.events",
                title="Get Agent Events",
                description="Fetch recent events for an agent workflow.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["task_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_events,
            ),
            "agent.recent": ToolSpec(
                name="agent.recent",
                title="Get Recent Agent Tasks",
                description="Fetch recent agent tasks visible to the current actor.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_recent,
            ),
            "agent.report": ToolSpec(
                name="agent.report",
                title="Get Agent Report Preview",
                description="Fetch report preview and raw URL for a completed agent workflow.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "max_chars": {"type": "integer"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["task_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_report,
            ),
            "agent.bundle": ToolSpec(
                name="agent.bundle",
                title="Get Canonical Execution Bundle",
                description="Fetch status, events, report, approval, and capability snapshot for one agent workflow.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "max_chars": {"type": "integer"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["task_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_bundle,
            ),
            "agent.handoff": ToolSpec(
                name="agent.handoff",
                title="Get Operator Handoff Packet",
                description="Fetch a compact operator handoff packet for blocked, approval-pending, or completed workflows.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "max_chars": {"type": "integer"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["task_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_agent_handoff,
            ),
            "job.list": ToolSpec(
                name="job.list",
                title="List Stage 12 Jobs",
                description="List Stage 12 job templates with executable status, compatible profiles, and runtime surfaces.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "profile_id": {"type": "string"},
                        "include_disabled": {"type": "boolean"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_job_list,
            ),
            "job.describe": ToolSpec(
                name="job.describe",
                title="Describe Stage 12 Job",
                description="Describe one Stage 12 job template, including input schema, compatible profile, capability packs, and examples.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string"},
                        "profile_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["template_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_job_describe,
            ),
            "job.run": ToolSpec(
                name="job.run",
                title="Run Stage 12 Job",
                description="Run a bounded Stage 12 job template and return status, events, report, and optional bundle/handoff evidence.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string"},
                        "profile_id": {"type": "string"},
                        "input": {"type": "object"},
                        "requested_by": {"type": "string"},
                        "auto_run": {"type": "boolean"},
                        "include_bundle": {"type": "boolean"},
                        "include_handoff": {"type": "boolean"},
                        "max_chars": {"type": "integer"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["template_id", "profile_id", "input", "requested_by", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_job_run,
            ),
            "approval.list": ToolSpec(
                name="approval.list",
                title="List Approvals",
                description="List approval queue items for approvers or admins.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "approver_group": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_approval_list,
            ),
            "approval.get": ToolSpec(
                name="approval.get",
                title="Get Approval Detail",
                description="Fetch one approval queue item with action history.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "queue_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["queue_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_approval_get,
            ),
            "approval.approve": ToolSpec(
                name="approval.approve",
                title="Approve Queue Item",
                description="Approve a pending queue item and resume the workflow.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "queue_id": {"type": "string"},
                        "acted_by": {"type": "string"},
                        "comment": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["queue_id", "acted_by"],
                    "additionalProperties": False,
                },
                handler=self._handle_approval_approve,
            ),
            "approval.reject": ToolSpec(
                name="approval.reject",
                title="Reject Queue Item",
                description="Reject a pending queue item and finish the workflow.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "queue_id": {"type": "string"},
                        "acted_by": {"type": "string"},
                        "comment": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["queue_id", "acted_by"],
                    "additionalProperties": False,
                },
                handler=self._handle_approval_reject,
            ),
            "catalog.list": ToolSpec(
                name="catalog.list",
                title="List Registered Execution Tools",
                description="List the policy-governed execution tools known to NewClaw.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "capability_family": {"type": "string"},
                        "external_system": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_list,
            ),
            "catalog.get": ToolSpec(
                name="catalog.get",
                title="Get Execution Tool Capability",
                description="Fetch the capability metadata for one registered execution tool.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tool_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["tool_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_get,
            ),
            "catalog.manifest": ToolSpec(
                name="catalog.manifest",
                title="Get Orchestration Capability Manifest",
                description="Fetch the current capability manifest for NestClaw orchestration runtime.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_manifest,
            ),
            "catalog.create_draft": ToolSpec(
                name="catalog.create_draft",
                title="Create Tool Registration Draft",
                description="Create a reviewable draft for a new execution tool capability.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "requested_by": {"type": "string"},
                        "request_text": {"type": "string"},
                        "tool_id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "adapter": {"type": "string"},
                        "method": {"type": "string"},
                        "action_type": {"type": "string"},
                        "external_system": {"type": "string"},
                        "capability_family": {"type": "string"},
                        "required_payload_fields": {"type": "array", "items": {"type": "string"}},
                        "default_risk_level": {"type": "string"},
                        "default_approval_required": {"type": "boolean"},
                        "supports_dry_run": {"type": "boolean"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["requested_by", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_create_draft,
            ),
            "catalog.get_draft": ToolSpec(
                name="catalog.get_draft",
                title="Get Tool Registration Draft",
                description="Fetch a previously generated tool registration draft.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["draft_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_get_draft,
            ),
            "catalog.validate_draft": ToolSpec(
                name="catalog.validate_draft",
                title="Validate Tool Registration Draft",
                description="Validate a tool draft against registry governance rules.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["draft_id", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_validate_draft,
            ),
            "catalog.apply_draft": ToolSpec(
                name="catalog.apply_draft",
                title="Apply Tool Registration Draft",
                description="Approve and apply a reviewed tool draft into the runtime overlay registry.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string"},
                        "acted_by": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["draft_id", "acted_by", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_apply_draft,
            ),
            "catalog.rollback_tool": ToolSpec(
                name="catalog.rollback_tool",
                title="Rollback Applied Tool Change",
                description="Rollback the latest applied overlay change for a tool.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tool_id": {"type": "string"},
                        "acted_by": {"type": "string"},
                        "actor_id": {"type": "string"},
                        "actor_role": {"type": "string", "enum": sorted(VALID_ROLES)},
                    },
                    "required": ["tool_id", "acted_by", "actor_id"],
                    "additionalProperties": False,
                },
                handler=self._handle_catalog_rollback_tool,
            ),
        }

    def _tool_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
            "structuredContent": payload,
            "isError": "error" in payload,
        }

    def _jsonrpc_result(self, request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}

    def _jsonrpc_error(self, request_id: Any, code: int, message: str, *, data: Any = None) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}

    def _negotiated_protocol_version(self, requested: str | None) -> str:
        if requested in SUPPORTED_PROTOCOL_VERSIONS:
            return str(requested)
        return SUPPORTED_PROTOCOL_VERSIONS[0]

    def _tool_actor(self, arguments: dict[str, Any], *, default_role: str) -> ActorContext:
        actor_id = str(arguments.get("actor_id") or arguments.get("requested_by") or arguments.get("acted_by") or "").strip()
        actor_role = str(arguments.get("actor_role") or default_role).strip().lower()
        return _actor_context(actor_id, actor_role)

    def _handle_agent_submit(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        payload = {
            "request_text": arguments.get("request_text"),
            "requested_by": arguments.get("requested_by"),
            "task_kind": arguments.get("task_kind", "auto"),
            "title": arguments.get("title"),
            "metadata": dict(arguments.get("metadata") or {}),
            "auto_run": bool(arguments.get("auto_run", True)),
            "incident_run_mode": arguments.get("incident_run_mode", "dry-run"),
        }
        return _invoke(self.orchestration_service.submit_agent, payload, actor)

    def _handle_agent_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.orchestration_service.agent_status, str(arguments.get("task_id") or ""), actor)

    def _handle_agent_events(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.orchestration_service.agent_events, str(arguments.get("task_id") or ""), actor)

    def _handle_agent_recent(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        limit = int(arguments.get("limit") or 10)
        return _invoke(self.orchestration_service.agent_recent, actor, limit=limit)

    def _handle_agent_report(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        max_chars = int(arguments.get("max_chars") or 4000)
        return _invoke(
            self.orchestration_service.agent_report,
            str(arguments.get("task_id") or ""),
            actor,
            max_chars=max_chars,
        )

    def _handle_agent_bundle(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        max_chars = int(arguments.get("max_chars") or 4000)
        return _invoke(
            self.orchestration_service.agent_bundle,
            str(arguments.get("task_id") or ""),
            actor,
            max_chars=max_chars,
        )

    def _handle_agent_handoff(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        max_chars = int(arguments.get("max_chars") or 1600)
        return _invoke(
            self.orchestration_service.agent_handoff,
            str(arguments.get("task_id") or ""),
            actor,
            max_chars=max_chars,
        )

    def _handle_job_list(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self._tool_actor(arguments, default_role="requester")
        return _invoke(
            job_list_payload,
            profile_id=arguments.get("profile_id"),
            include_disabled=bool(arguments.get("include_disabled", False)),
        )

    def _handle_job_describe(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self._tool_actor(arguments, default_role="requester")
        return _invoke(
            job_describe_payload,
            template_id=str(arguments.get("template_id") or ""),
            profile_id=arguments.get("profile_id"),
        )

    def _handle_job_run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(
            run_stage12_job,
            orchestration_service=self.orchestration_service,
            actor=actor,
            template_id=str(arguments.get("template_id") or ""),
            profile_id=str(arguments.get("profile_id") or ""),
            input_payload=dict(arguments.get("input") or {}),
            requested_by=str(arguments.get("requested_by") or ""),
            include_bundle=bool(arguments.get("include_bundle", False)),
            include_handoff=bool(arguments.get("include_handoff", False)),
            max_chars=int(arguments.get("max_chars") or 4000),
            auto_run=bool(arguments.get("auto_run", True)),
        )

    def _handle_approval_list(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="approver")
        return _invoke(
            self.approval_service.list_approvals,
            arguments.get("status"),
            arguments.get("approver_group"),
            actor,
        )

    def _handle_approval_get(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="approver")
        return _invoke(self.approval_service.get_approval, str(arguments.get("queue_id") or ""), actor)

    def _handle_approval_approve(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="approver")
        payload = {"acted_by": arguments.get("acted_by"), "comment": arguments.get("comment")}
        return _invoke(self.approval_service.approve, str(arguments.get("queue_id") or ""), payload, actor)

    def _handle_approval_reject(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="approver")
        payload = {"acted_by": arguments.get("acted_by"), "comment": arguments.get("comment")}
        return _invoke(self.approval_service.reject, str(arguments.get("queue_id") or ""), payload, actor)

    def _handle_catalog_list(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(
            self.tool_catalog_service.list_tools,
            arguments.get("capability_family"),
            arguments.get("external_system"),
            actor,
        )

    def _handle_catalog_get(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.tool_catalog_service.get_tool, str(arguments.get("tool_id") or ""), actor)

    def _handle_catalog_manifest(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.capability_manifest_service.get_manifest, actor)

    def _handle_catalog_create_draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.tool_draft_service.create_draft, dict(arguments), actor)

    def _handle_catalog_get_draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.tool_draft_service.get_draft, str(arguments.get("draft_id") or ""), actor)

    def _handle_catalog_validate_draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="requester")
        return _invoke(self.tool_draft_service.validate_draft, str(arguments.get("draft_id") or ""), actor)

    def _handle_catalog_apply_draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="approver")
        payload = {"acted_by": arguments.get("acted_by")}
        result = _invoke(self.tool_draft_service.apply_draft, str(arguments.get("draft_id") or ""), payload, actor)
        if "error" not in result:
            self.tool_catalog_service = build_tool_catalog_service()
        return result

    def _handle_catalog_rollback_tool(self, arguments: dict[str, Any]) -> dict[str, Any]:
        actor = self._tool_actor(arguments, default_role="approver")
        payload = {"acted_by": arguments.get("acted_by")}
        result = _invoke(self.tool_draft_service.rollback_tool, str(arguments.get("tool_id") or ""), payload, actor)
        if "error" not in result:
            self.tool_catalog_service = build_tool_catalog_service()
        return result

    def process_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = str(message.get("method") or "")
        request_id = message.get("id")
        params = dict(message.get("params") or {})

        if method == "initialize":
            self.initialized = True
            protocol_version = self._negotiated_protocol_version(str(params.get("protocolVersion") or ""))
            return self._jsonrpc_result(
                request_id,
                {
                    "protocolVersion": protocol_version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    "instructions": (
                        "NestClaw MCP stdio baseline. Use requester/reviewer for observe loops; "
                        "approver/admin only for elevated approval or catalog controls."
                    ),
                },
            )

        if method == "notifications/initialized":
            self.initialized = True
            return None

        if method == "ping":
            return self._jsonrpc_result(request_id, {})

        if not self.initialized:
            return self._jsonrpc_error(request_id, -32002, "server not initialized")

        if method == "tools/list":
            tools = [
                {
                    "name": tool.name,
                    "title": tool.title,
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                }
                for tool in self.tools.values()
            ]
            return self._jsonrpc_result(request_id, {"tools": tools})

        if method == "tools/call":
            tool_name = str(params.get("name") or "")
            tool = self.tools.get(tool_name)
            if not tool:
                return self._jsonrpc_error(request_id, -32601, f"tool not found: {tool_name}")
            arguments = dict(params.get("arguments") or {})
            return self._jsonrpc_result(request_id, self._tool_result(tool.handler(arguments)))

        if method.startswith("notifications/"):
            return None

        return self._jsonrpc_error(request_id, -32601, f"method not found: {method}")


def read_message(infile: Any) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = infile.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        name, _, value = line.decode("utf-8").partition(":")
        headers[name.strip().lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None
    body = infile.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(outfile: Any, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    outfile.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
    outfile.write(body)
    outfile.flush()


def serve_forever(server: NewClawMcpServer, *, infile: Any, outfile: Any) -> int:
    while True:
        message = read_message(infile)
        if message is None:
            return 0
        response = server.process_message(message)
        if response is not None:
            write_message(outfile, response)


def main() -> int:
    server = NewClawMcpServer()
    return serve_forever(server, infile=sys.stdin.buffer, outfile=sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(main())
