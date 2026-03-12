from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping
from urllib import error, request

from app.model_registry import ModelRegistry, select_provider


INTENT_INCIDENT_HINTS = {
    "incident",
    "outage",
    "sev1",
    "sev2",
    "sev-1",
    "sev-2",
    "degraded",
    "downtime",
    "latency",
    "on-call",
    "rollback",
    "alarm",
    "장애",
    "알람",
    "장애대응",
}
SENSITIVITY_HINTS = {"sensitive", "confidential", "내부 전용", "민감"}
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class IntentClassification:
    resolved_kind: str
    source: str
    confidence: float | None = None
    rationale: str | None = None
    provider_selection: dict[str, Any] | None = None
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "resolved_kind": self.resolved_kind,
            "source": self.source,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "provider_selection": self.provider_selection,
            "fallback_reason": self.fallback_reason,
        }


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value).strip()


def _looks_like_incident(request_text: str, metadata: Mapping[str, Any]) -> bool:
    if any(key in metadata for key in ("incident_id", "service", "severity", "policy_profile", "time_window")):
        return True
    haystack = f"{request_text} {_flatten_text(dict(metadata))}".lower()
    return any(token in haystack for token in INTENT_INCIDENT_HINTS)


def _heuristic_resolved_kind(request_text: str, metadata: Mapping[str, Any]) -> str:
    return "incident" if _looks_like_incident(request_text, metadata) else "task"


def _infer_sensitivity(request_text: str, metadata: Mapping[str, Any]) -> str:
    explicit = str(metadata.get("sensitivity") or "").strip().lower()
    if explicit in {"low", "high"}:
        return explicit
    haystack = f"{request_text} {_flatten_text(dict(metadata))}".lower()
    if any(token in haystack for token in (hint.lower() for hint in SENSITIVITY_HINTS)):
        return "high"
    return "high" if _looks_like_incident(request_text, metadata) else "low"


def _external_send_requested(request_text: str, metadata: Mapping[str, Any]) -> bool:
    haystack = f"{request_text} {_flatten_text(dict(metadata))}".lower()
    return any(token in haystack for token in ("외부 전송", "external send", "send externally", "http://", "https://"))


def _is_truthy(raw: str | None, *, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if not text:
        raise ValueError("empty classifier response")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("classifier response did not contain json object")
        payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("classifier response must be a json object")
    return payload


def _build_intent_prompt(request_text: str, metadata: Mapping[str, Any]) -> str:
    metadata_text = json.dumps(dict(metadata), ensure_ascii=False, sort_keys=True)
    return (
        "You classify orchestration requests.\n"
        'Respond with JSON only: {"task_kind":"task|incident","confidence":0..1,"rationale":"..."}.\n'
        "Choose incident for outage, degradation, alarms, rollback, on-call, or service-impact requests.\n"
        "Choose task for meeting summaries, reports, and generic work delegation.\n"
        f"request_text: {request_text}\n"
        f"metadata: {metadata_text}\n"
    )


def _call_ollama_generate(*, base_url: str, model: str, prompt: str, timeout_seconds: float) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    req = request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.URLError as exc:
        raise RuntimeError(f"intent classifier call failed: {exc}") from exc
    parsed = json.loads(body)
    response_text = str(parsed.get("response") or "").strip()
    if not response_text:
        raise RuntimeError("intent classifier response was empty")
    return response_text


class IntentClassifier:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def classify(self, request_text: str, metadata: Mapping[str, Any] | None = None) -> IntentClassification:
        metadata_map = dict(metadata or {})
        provider_selection = select_provider(
            self.registry,
            sensitivity=_infer_sensitivity(request_text, metadata_map),
            task_type="classify_intent",
            external_send=_external_send_requested(request_text, metadata_map),
        ).as_dict()
        heuristic_kind = _heuristic_resolved_kind(request_text, metadata_map)

        if not _is_truthy(os.getenv("NEWCLAW_ENABLE_LLM_INTENT"), default=False):
            return IntentClassification(
                resolved_kind=heuristic_kind,
                source="heuristic_fallback",
                confidence=0.55,
                rationale="live intent classifier disabled",
                provider_selection=provider_selection,
            )

        provider_type = str(provider_selection.get("provider_type") or "")
        engine = str(provider_selection.get("engine") or "")
        if provider_type != "local" or engine != "ollama":
            return IntentClassification(
                resolved_kind=heuristic_kind,
                source="heuristic_fallback",
                confidence=0.55,
                rationale="selected provider does not support live intent classification",
                provider_selection=provider_selection,
                fallback_reason="unsupported_provider",
            )

        model = str(provider_selection.get("model") or "").strip()
        if not model:
            return IntentClassification(
                resolved_kind=heuristic_kind,
                source="heuristic_fallback",
                confidence=0.55,
                rationale="selected provider model is missing",
                provider_selection=provider_selection,
                fallback_reason="missing_model",
            )

        try:
            response_text = _call_ollama_generate(
                base_url=os.getenv("NEWCLAW_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
                model=model,
                prompt=_build_intent_prompt(request_text, metadata_map),
                timeout_seconds=float(os.getenv("NEWCLAW_INTENT_CLASSIFIER_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))),
            )
            payload = _extract_json_object(response_text)
            resolved_kind = str(payload.get("task_kind") or "").strip().lower()
            if resolved_kind not in {"task", "incident"}:
                raise ValueError(f"unsupported task_kind from llm: {resolved_kind}")
            confidence_raw = payload.get("confidence")
            confidence = float(confidence_raw) if confidence_raw is not None else None
            rationale = str(payload.get("rationale") or "llm classified request").strip() or "llm classified request"
            return IntentClassification(
                resolved_kind=resolved_kind,
                source="llm",
                confidence=confidence,
                rationale=rationale,
                provider_selection=provider_selection,
            )
        except Exception as exc:
            return IntentClassification(
                resolved_kind=heuristic_kind,
                source="llm_error_fallback",
                confidence=0.55,
                rationale="llm classification failed; fallback heuristic applied",
                provider_selection=provider_selection,
                fallback_reason=str(exc),
            )
