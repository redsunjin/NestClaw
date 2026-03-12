from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.intent_classifier import IntentClassifier
from app.model_registry import ModelRegistry, ProviderConfig, load_model_registry


class TestIntentClassifierContract(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_model_registry()
        self.classifier = IntentClassifier(self.registry)

    def test_disabled_live_classifier_uses_heuristic_fallback(self) -> None:
        with patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_INTENT": "0"}, clear=False):
            result = self.classifier.classify(
                "billing-api 장애 대응 티켓을 생성해줘",
                {"service": "billing-api", "time_window": "15m"},
            )

        self.assertEqual(result.resolved_kind, "incident")
        self.assertEqual(result.source, "heuristic_fallback")
        self.assertEqual(result.provider_selection["provider_id"], "local_lmstudio")
        self.assertIsNone(result.fallback_reason)

    def test_live_classifier_uses_llm_result_when_response_is_valid(self) -> None:
        with (
            patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_INTENT": "1"}, clear=False),
            patch(
                "app.intent_classifier._detect_openai_compatible_model",
                return_value="lmstudio-loaded-model",
            ),
            patch(
                "app.intent_classifier._call_openai_compatible_chat",
                return_value='{"task_kind":"task","confidence":0.91,"rationale":"meeting summary request"}',
            ),
        ):
            result = self.classifier.classify("운영회의 메모를 요약해줘", {"meeting_title": "ops sync"})

        self.assertEqual(result.resolved_kind, "task")
        self.assertEqual(result.source, "llm")
        self.assertAlmostEqual(float(result.confidence or 0), 0.91, places=2)
        self.assertEqual(result.provider_selection["provider_id"], "local_lmstudio")

    def test_live_classifier_falls_back_when_response_is_not_json(self) -> None:
        with (
            patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_INTENT": "1"}, clear=False),
            patch("app.intent_classifier._detect_openai_compatible_model", return_value="lmstudio-loaded-model"),
            patch("app.intent_classifier._call_openai_compatible_chat", return_value="not-json"),
        ):
            result = self.classifier.classify("운영회의 메모를 요약해줘", {"meeting_title": "ops sync"})

        self.assertEqual(result.resolved_kind, "task")
        self.assertEqual(result.source, "llm_error_fallback")
        self.assertIn("json object", str(result.fallback_reason))

    def test_live_classifier_autodetects_lmstudio_model_when_config_is_auto(self) -> None:
        with (
            patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_INTENT": "1"}, clear=False),
            patch("app.intent_classifier._detect_openai_compatible_model", return_value="qwen2.5-14b-instruct"),
            patch(
                "app.intent_classifier._call_openai_compatible_chat",
                return_value='{"task_kind":"incident","confidence":0.88,"rationale":"outage-like request"}',
            ) as call_mock,
        ):
            result = self.classifier.classify("billing-api 장애 대응 티켓을 생성해줘", {"service": "billing-api"})

        self.assertEqual(result.source, "llm")
        self.assertEqual(result.resolved_kind, "incident")
        self.assertEqual(call_mock.call_args.kwargs["model"], "qwen2.5-14b-instruct")

    def test_live_classifier_falls_back_for_unsupported_provider(self) -> None:
        api_only_registry = ModelRegistry(
            version=1,
            providers=(
                ProviderConfig(
                    provider_id="api_only",
                    provider_type="api",
                    enabled=True,
                    engine="openai",
                    model="gpt-4.1-mini",
                    purpose="general_reasoning",
                ),
            ),
            routing_rules=(),
        )
        classifier = IntentClassifier(api_only_registry)

        with patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_INTENT": "1"}, clear=False):
            result = classifier.classify("운영회의 메모를 요약해줘", {"meeting_title": "ops sync"})

        self.assertEqual(result.resolved_kind, "task")
        self.assertEqual(result.source, "heuristic_fallback")
        self.assertEqual(result.fallback_reason, "unsupported_provider")
        self.assertEqual(result.provider_selection["provider_id"], "api_only")


if __name__ == "__main__":
    unittest.main()
