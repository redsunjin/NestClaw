from __future__ import annotations

import unittest
from unittest.mock import patch

from app.model_registry import load_model_registry, select_provider
from app.provider_invoker import ProviderInvoker


def _fallback_renderer(task_input: dict[str, object]) -> str:
    return (
        "# 회의 결과 요약\n\n"
        "## 핵심 논점\n- fallback\n\n"
        "## 액션 아이템\n| 항목 | 담당자 | 기한 | 우선순위 | 상태 |\n|---|---|---|---|---|\n"
        "| Action 1 | TBD | TBD | Medium | Open |\n\n"
        "## 확인 필요\n- none\n"
    )


class TestProviderInvokerContract(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_model_registry()
        self.invoker = ProviderInvoker()
        self.selection = select_provider(
            self.registry,
            sensitivity="low",
            task_type="summarize",
            external_send=False,
        ).as_dict()
        self.task_input = {
            "meeting_title": "ops sync",
            "meeting_date": "2026-03-12",
            "participants": ["Kim"],
            "notes": "general summary only",
        }

    def test_summary_invocation_falls_back_when_live_disabled(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            result = self.invoker.invoke_meeting_summary(
                task_input=self.task_input,
                provider_selection=self.selection,
                fallback_renderer=_fallback_renderer,
            )
        self.assertEqual(result.invocation.result_source, "template_fallback")
        self.assertEqual(result.invocation.fallback_reason, "live_summary_disabled")
        self.assertIn("# 회의 결과 요약", result.output_text)

    def test_summary_invocation_can_return_live_provider_output(self) -> None:
        with patch.dict(
            "os.environ",
            {"NEWCLAW_ENABLE_LLM_SUMMARY": "1", "NEWCLAW_OPENAI_BASE_URL": "http://127.0.0.1:1234"},
            clear=False,
        ):
            with patch(
                "app.provider_invoker._call_summary_openai_compatible_chat",
                return_value=(
                    "# 회의 결과 요약\n\n"
                    "## 핵심 논점\n- live summary\n\n"
                    "## 액션 아이템\n| 항목 | 담당자 | 기한 | 우선순위 | 상태 |\n|---|---|---|---|---|\n"
                    "| Action 1 | Kim | 2026-03-13 | High | Open |\n\n"
                    "## 확인 필요\n- verify\n"
                ),
            ):
                result = self.invoker.invoke_meeting_summary(
                    task_input=self.task_input,
                    provider_selection=self.selection,
                    fallback_renderer=_fallback_renderer,
                )
        self.assertEqual(result.invocation.result_source, "live_provider")
        self.assertTrue(result.invocation.invoked)
        self.assertIn("live summary", result.output_text)


if __name__ == "__main__":
    unittest.main()
