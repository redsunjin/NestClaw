from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping, Sequence
from urllib import error, request

from app.intent_classifier import (
    DEFAULT_LMSTUDIO_BASE_URL,
    DEFAULT_OLLAMA_BASE_URL,
    _call_ollama_generate,
    _detect_openai_compatible_model,
    _extract_json_object,
)
from app.model_registry import ModelRegistry, select_provider
from app.provider_invoker import DEFAULT_OPENAI_BASE_URL
from app.tool_registry import ToolCapability


DEFAULT_PLANNER_TIMEOUT_SECONDS = 8.0
DEFAULT_PLANNER_TASK_TYPE = "plan_actions"
SUMMARY_TOOL_ID = "internal.summary.generate"
SLACK_TOOL_ID = "slack.message.send"
NOTIFY_HINTS = {
    "slack",
    "notify",
    "notification",
    "share",
    "announce",
    "알려줘",
    "공유",
    "공지",
    "슬랙",
}


def _is_truthy(raw: str | None, *, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_openai_compatible_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _call_planner_openai_compatible_chat(
    *,
    base_url: str,
    model: str,
    prompt: str,
    timeout_seconds: float,
    api_key: str | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict JSON-only enterprise orchestration planner."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = request.Request(
        f"{_normalize_openai_compatible_base_url(base_url)}/chat/completions",
        method="POST",
        headers=headers,
        data=json.dumps(payload).encode("utf-8"),
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.URLError as exc:
        raise RuntimeError(f"planner provider call failed: {exc}") from exc
    parsed = json.loads(body)
    choices = parsed.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("planner response did not include choices")
    message = dict((choices[0] or {}).get("message") or {})
    response_text = str(message.get("content") or "").strip()
    if not response_text:
        raise RuntimeError("planner response was empty")
    return response_text


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value).strip()


def _looks_like_notify_request(request_text: str, metadata: Mapping[str, Any]) -> bool:
    haystack = f"{request_text} {_flatten_text(dict(metadata))}".lower()
    return any(token in haystack for token in NOTIFY_HINTS)


def _build_planner_prompt(
    *,
    request_text: str,
    task_input: Mapping[str, Any],
    metadata: Mapping[str, Any],
    available_tools: Sequence[ToolCapability],
    default_notify_channel: str | None,
) -> str:
    tools_payload = [
        {
            "tool_id": item.tool_id,
            "title": item.title,
            "description": item.description,
            "required_payload_fields": list(item.required_payload_fields),
            "adapter": item.adapter,
            "method": item.method,
        }
        for item in available_tools
    ]
    request_payload = {
        "request_text": request_text,
        "task_input": dict(task_input),
        "metadata": dict(metadata),
        "default_notify_channel": default_notify_channel,
    }
    return (
        "Plan a task workflow using the allowed tools only.\n"
        "Respond with JSON only.\n"
        'Schema: {"actions":[{"tool_id":"...","reason":"...","payload_overrides":{...}}],"confidence":0.0,"rationale":"..."}\n'
        f"Rules:\n"
        f"- The first action must be {SUMMARY_TOOL_ID}.\n"
        f"- Use {SLACK_TOOL_ID} only when a notification/share intent exists and a channel is available.\n"
        f"- Do not invent tools outside the allowed tool list.\n"
        f"- Keep the plan short and executable.\n"
        f"Allowed tools: {json.dumps(tools_payload, ensure_ascii=False)}\n"
        f"Request context: {json.dumps(request_payload, ensure_ascii=False)}\n"
    )


@dataclass(frozen=True)
class PlannerAction:
    tool_id: str
    reason: str | None = None
    payload_overrides: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "reason": self.reason,
            "payload_overrides": dict(self.payload_overrides or {}),
        }


@dataclass(frozen=True)
class TaskPlanningDecision:
    actions: tuple[PlannerAction, ...]
    source: str
    rationale: str | None = None
    confidence: float | None = None
    provider_selection: dict[str, Any] | None = None
    fallback_reason: str | None = None
    degraded_mode: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "actions": [item.as_dict() for item in self.actions],
            "source": self.source,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "provider_selection": self.provider_selection,
            "fallback_reason": self.fallback_reason,
            "degraded_mode": self.degraded_mode,
        }


class AgentPlanner:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def _fallback_plan(
        self,
        *,
        request_text: str,
        metadata: Mapping[str, Any],
        available_tools: Sequence[ToolCapability],
        default_notify_channel: str | None,
        provider_selection: Mapping[str, Any],
        source: str,
        rationale: str,
        fallback_reason: str | None = None,
    ) -> TaskPlanningDecision:
        tools_by_id = {item.tool_id: item for item in available_tools}
        actions = [PlannerAction(tool_id=SUMMARY_TOOL_ID, reason="baseline summary action")]
        if (
            default_notify_channel
            and SLACK_TOOL_ID in tools_by_id
            and _looks_like_notify_request(request_text, metadata)
        ):
            actions.append(
                PlannerAction(
                    tool_id=SLACK_TOOL_ID,
                    reason="notify/share intent detected",
                    payload_overrides={"channel": default_notify_channel},
                )
            )
        return TaskPlanningDecision(
            actions=tuple(actions),
            source=source,
            rationale=rationale,
            confidence=0.55,
            provider_selection=dict(provider_selection),
            fallback_reason=fallback_reason,
            degraded_mode=True,
        )

    def _normalize_actions(
        self,
        *,
        raw_actions: Any,
        allowed_tools: Mapping[str, ToolCapability],
        default_notify_channel: str | None,
    ) -> tuple[PlannerAction, ...]:
        if not isinstance(raw_actions, list) or not raw_actions:
            raise ValueError("planner response must include a non-empty actions list")

        actions: list[PlannerAction] = []
        seen: set[str] = set()
        for raw_item in raw_actions:
            if not isinstance(raw_item, Mapping):
                raise ValueError("planner action must be an object")
            tool_id = str(raw_item.get("tool_id") or "").strip()
            if tool_id not in allowed_tools:
                raise ValueError(f"unsupported tool_id: {tool_id}")
            if tool_id in seen:
                continue
            seen.add(tool_id)
            payload_overrides = dict(raw_item.get("payload_overrides") or raw_item.get("payload") or {})
            if tool_id == SLACK_TOOL_ID:
                channel = str(payload_overrides.get("channel") or default_notify_channel or "").strip()
                if not channel:
                    raise ValueError("slack action requires a channel")
                payload_overrides["channel"] = channel
            actions.append(
                PlannerAction(
                    tool_id=tool_id,
                    reason=str(raw_item.get("reason") or "").strip() or None,
                    payload_overrides=payload_overrides,
                )
            )

        if not actions:
            raise ValueError("planner response produced no actionable tools")
        if actions[0].tool_id != SUMMARY_TOOL_ID:
            raise ValueError(f"first action must be {SUMMARY_TOOL_ID}")
        return tuple(actions)

    def plan_task_actions(
        self,
        *,
        request_text: str,
        task_input: Mapping[str, Any],
        metadata: Mapping[str, Any],
        available_tools: Sequence[ToolCapability],
        sensitivity: str,
        external_send: bool,
        default_notify_channel: str | None = None,
    ) -> TaskPlanningDecision:
        provider_selection = select_provider(
            self.registry,
            sensitivity=sensitivity,
            task_type=DEFAULT_PLANNER_TASK_TYPE,
            external_send=external_send,
        ).as_dict()

        if not _is_truthy(os.getenv("NEWCLAW_ENABLE_LLM_PLANNER"), default=False):
            return self._fallback_plan(
                request_text=request_text,
                metadata=metadata,
                available_tools=available_tools,
                default_notify_channel=default_notify_channel,
                provider_selection=provider_selection,
                source="heuristic_fallback",
                rationale="live planner disabled",
            )

        provider_type = str(provider_selection.get("provider_type") or "").strip().lower()
        engine = str(provider_selection.get("engine") or "").strip().lower()
        if provider_type not in {"local", "api"} or engine not in {"lmstudio", "ollama", "openai"}:
            return self._fallback_plan(
                request_text=request_text,
                metadata=metadata,
                available_tools=available_tools,
                default_notify_channel=default_notify_channel,
                provider_selection=provider_selection,
                source="heuristic_fallback",
                rationale="selected planner provider is unsupported",
                fallback_reason="unsupported_provider",
            )

        timeout_seconds = float(os.getenv("NEWCLAW_LLM_PLANNER_TIMEOUT", str(DEFAULT_PLANNER_TIMEOUT_SECONDS)))
        prompt = _build_planner_prompt(
            request_text=request_text,
            task_input=task_input,
            metadata=metadata,
            available_tools=available_tools,
            default_notify_channel=default_notify_channel,
        )
        try:
            model = str(provider_selection.get("model") or "").strip()
            if engine == "lmstudio" and model.lower() in {"", "auto"}:
                model = _detect_openai_compatible_model(
                    base_url=os.getenv("NEWCLAW_LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_BASE_URL),
                    timeout_seconds=timeout_seconds,
                    api_key=os.getenv("NEWCLAW_LMSTUDIO_API_KEY"),
                )
            if not model:
                raise RuntimeError("missing_model")

            if engine == "ollama":
                response_text = _call_ollama_generate(
                    base_url=os.getenv("NEWCLAW_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
                    model=model,
                    prompt=prompt,
                    timeout_seconds=timeout_seconds,
                )
            elif engine == "lmstudio":
                response_text = _call_planner_openai_compatible_chat(
                    base_url=os.getenv("NEWCLAW_LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_BASE_URL),
                    model=model,
                    prompt=prompt,
                    timeout_seconds=timeout_seconds,
                    api_key=os.getenv("NEWCLAW_LMSTUDIO_API_KEY"),
                )
            else:
                response_text = _call_planner_openai_compatible_chat(
                    base_url=os.getenv("NEWCLAW_OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL),
                    model=model,
                    prompt=prompt,
                    timeout_seconds=timeout_seconds,
                    api_key=os.getenv("NEWCLAW_OPENAI_API_KEY"),
                )

            payload = _extract_json_object(response_text)
            actions = self._normalize_actions(
                raw_actions=payload.get("actions"),
                allowed_tools={item.tool_id: item for item in available_tools},
                default_notify_channel=default_notify_channel,
            )
            confidence_raw = payload.get("confidence")
            confidence = float(confidence_raw) if confidence_raw is not None else None
            rationale = str(payload.get("rationale") or "llm planner selected actions").strip() or "llm planner selected actions"
            provider_selection = dict(provider_selection)
            provider_selection["model"] = model
            return TaskPlanningDecision(
                actions=actions,
                source="llm",
                rationale=rationale,
                confidence=confidence,
                provider_selection=provider_selection,
                degraded_mode=False,
            )
        except Exception as exc:
            return self._fallback_plan(
                request_text=request_text,
                metadata=metadata,
                available_tools=available_tools,
                default_notify_channel=default_notify_channel,
                provider_selection=provider_selection,
                source="llm_error_fallback",
                rationale="planner call failed; deterministic plan applied",
                fallback_reason=str(exc),
            )
