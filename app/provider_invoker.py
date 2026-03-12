from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Callable, Mapping
from urllib import error, request

from app.intent_classifier import (
    DEFAULT_LMSTUDIO_BASE_URL,
    DEFAULT_OLLAMA_BASE_URL,
    _call_ollama_generate,
    _detect_openai_compatible_model,
)


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_SUMMARY_TIMEOUT_SECONDS = 10.0


def _is_truthy(raw: str | None, *, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _build_meeting_summary_prompt(task_input: Mapping[str, Any]) -> str:
    meeting_title = str(task_input.get("meeting_title") or "N/A").strip()
    meeting_date = str(task_input.get("meeting_date") or "N/A").strip()
    participants = ", ".join(str(item).strip() for item in list(task_input.get("participants") or []) if str(item).strip()) or "N/A"
    notes = str(task_input.get("notes") or "").strip()
    return (
        "당신은 사내 업무 실행 에이전트의 회의 요약 작성기다.\n"
        "응답은 한국어 마크다운만 반환한다.\n"
        "다음 섹션을 반드시 포함한다:\n"
        "# 회의 결과 요약\n"
        "## 핵심 논점\n"
        "## 액션 아이템\n"
        "## 확인 필요\n"
        "액션 아이템에는 담당자/기한/우선순위/상태 컬럼이 있는 표를 포함한다.\n"
        f"회의 제목: {meeting_title}\n"
        f"회의 날짜: {meeting_date}\n"
        f"참석자: {participants}\n"
        f"원문 메모:\n{notes}\n"
    )


def _normalize_summary_markdown(raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        raise ValueError("provider returned empty summary")
    return text if text.endswith("\n") else f"{text}\n"


def _looks_like_meeting_summary(markdown: str) -> bool:
    required_tokens = ("# 회의 결과 요약", "## 핵심 논점", "## 액션 아이템")
    return all(token in markdown for token in required_tokens)


def _normalize_openai_compatible_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _call_summary_openai_compatible_chat(
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
            {"role": "system", "content": "You generate Korean markdown meeting summaries for enterprise workflows."},
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
        raise RuntimeError(f"summary provider call failed: {exc}") from exc
    parsed = json.loads(body)
    choices = parsed.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("summary provider response did not include choices")
    message = dict((choices[0] or {}).get("message") or {})
    response_text = str(message.get("content") or "").strip()
    if not response_text:
        raise RuntimeError("summary provider response was empty")
    return response_text


@dataclass(frozen=True)
class ProviderInvocation:
    task_type: str
    provider_id: str | None
    provider_type: str | None
    engine: str | None
    requested_model: str | None
    resolved_model: str | None
    invoked: bool
    result_source: str
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "engine": self.engine,
            "requested_model": self.requested_model,
            "resolved_model": self.resolved_model,
            "invoked": self.invoked,
            "result_source": self.result_source,
            "fallback_reason": self.fallback_reason,
        }


@dataclass(frozen=True)
class ProviderInvocationResult:
    output_text: str
    invocation: ProviderInvocation


class ProviderInvoker:
    def invoke_meeting_summary(
        self,
        *,
        task_input: Mapping[str, Any],
        provider_selection: Mapping[str, Any] | None,
        fallback_renderer: Callable[[Mapping[str, Any]], str],
    ) -> ProviderInvocationResult:
        selection = dict(provider_selection or {})
        fallback_text = fallback_renderer(task_input)
        task_type = str(selection.get("task_type") or "summarize")

        if not _is_truthy(os.getenv("NEWCLAW_ENABLE_LLM_SUMMARY"), default=False):
            return ProviderInvocationResult(
                output_text=fallback_text,
                invocation=ProviderInvocation(
                    task_type=task_type,
                    provider_id=selection.get("provider_id"),
                    provider_type=selection.get("provider_type"),
                    engine=selection.get("engine"),
                    requested_model=selection.get("model"),
                    resolved_model=selection.get("model"),
                    invoked=False,
                    result_source="template_fallback",
                    fallback_reason="live_summary_disabled",
                ),
            )

        try:
            output_text, resolved_model = self._invoke_selected_provider(
                task_input=task_input,
                provider_selection=selection,
            )
            normalized_output = _normalize_summary_markdown(output_text)
            if not _looks_like_meeting_summary(normalized_output):
                raise ValueError("provider output missing required summary sections")
            return ProviderInvocationResult(
                output_text=normalized_output,
                invocation=ProviderInvocation(
                    task_type=task_type,
                    provider_id=selection.get("provider_id"),
                    provider_type=selection.get("provider_type"),
                    engine=selection.get("engine"),
                    requested_model=selection.get("model"),
                    resolved_model=resolved_model,
                    invoked=True,
                    result_source="live_provider",
                    fallback_reason=None,
                ),
            )
        except Exception as exc:
            return ProviderInvocationResult(
                output_text=fallback_text,
                invocation=ProviderInvocation(
                    task_type=task_type,
                    provider_id=selection.get("provider_id"),
                    provider_type=selection.get("provider_type"),
                    engine=selection.get("engine"),
                    requested_model=selection.get("model"),
                    resolved_model=selection.get("model"),
                    invoked=False,
                    result_source="template_fallback",
                    fallback_reason=f"provider_call_failed:{exc}",
                ),
            )

    def _invoke_selected_provider(
        self,
        *,
        task_input: Mapping[str, Any],
        provider_selection: Mapping[str, Any],
    ) -> tuple[str, str]:
        provider_type = str(provider_selection.get("provider_type") or "").strip().lower()
        engine = str(provider_selection.get("engine") or "").strip().lower()
        requested_model = str(provider_selection.get("model") or "").strip()
        timeout_seconds = float(os.getenv("NEWCLAW_LLM_SUMMARY_TIMEOUT", str(DEFAULT_SUMMARY_TIMEOUT_SECONDS)))
        prompt = _build_meeting_summary_prompt(task_input)

        if provider_type not in {"local", "api"}:
            raise RuntimeError(f"unsupported_provider_type:{provider_type}")

        if engine == "lmstudio":
            model = requested_model
            if model.lower() in {"", "auto"}:
                model = _detect_openai_compatible_model(
                    base_url=os.getenv("NEWCLAW_LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_BASE_URL),
                    timeout_seconds=timeout_seconds,
                    api_key=os.getenv("NEWCLAW_LMSTUDIO_API_KEY"),
                )
            output = _call_summary_openai_compatible_chat(
                base_url=os.getenv("NEWCLAW_LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_BASE_URL),
                model=model,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
                api_key=os.getenv("NEWCLAW_LMSTUDIO_API_KEY"),
            )
            return output, model

        if engine == "ollama":
            if not requested_model:
                raise RuntimeError("missing_model")
            output = _call_ollama_generate(
                base_url=os.getenv("NEWCLAW_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
                model=requested_model,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
            )
            return output, requested_model

        if engine == "openai":
            base_url = os.getenv("NEWCLAW_OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
            api_key = os.getenv("NEWCLAW_OPENAI_API_KEY")
            if base_url.rstrip("/") == DEFAULT_OPENAI_BASE_URL.rstrip("/") and not api_key:
                raise RuntimeError("missing_api_key")
            if not requested_model:
                raise RuntimeError("missing_model")
            output = _call_summary_openai_compatible_chat(
                base_url=base_url,
                model=requested_model,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
                api_key=api_key,
            )
            return output, requested_model

        raise RuntimeError(f"unsupported_provider_engine:{engine}")
