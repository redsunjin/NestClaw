from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.agent_planner import AgentPlanner
from app.model_registry import ModelRegistry, ProviderConfig, RoutingRule, load_model_registry
from app.tool_registry import ToolCapability


SUMMARY_TOOL = ToolCapability(
    tool_id="internal.summary.generate",
    title="Generate meeting summary report",
    description="Generate meeting summary report",
    adapter="provider_invoker",
    method="summary.generate",
    action_type="internal_summary_generate",
    external_system="internal",
    capability_family="content_generation",
    default_risk_level="low",
    default_approval_required=False,
    supports_dry_run=False,
    required_payload_fields=("meeting_title", "meeting_date", "participants", "notes"),
)
SLACK_TOOL = ToolCapability(
    tool_id="slack.message.send",
    title="Send Slack message",
    description="Send Slack message",
    adapter="slack_api",
    method="message.send",
    action_type="slack_message_send",
    external_system="slack",
    capability_family="messaging",
    default_risk_level="medium",
    default_approval_required=False,
    supports_dry_run=True,
    required_payload_fields=("channel", "text"),
)
TICKET_TOOL = ToolCapability(
    tool_id="redmine.issue.create",
    title="Create follow-up ticket",
    description="Create a Redmine follow-up issue",
    adapter="redmine_mcp",
    method="issue.create",
    action_type="redmine_issue_create",
    external_system="redmine",
    capability_family="ticketing",
    default_risk_level="medium",
    default_approval_required=False,
    supports_dry_run=True,
    required_payload_fields=("project_id", "subject", "description", "priority"),
)


class TestAgentPlannerContract(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_model_registry()
        self.planner = AgentPlanner(self.registry)
        self.task_input = {
            "meeting_title": "ops sync",
            "meeting_date": "2026-03-13",
            "participants": ["Kim"],
            "notes": "주간 운영회의 메모",
        }

    def test_disabled_planner_uses_heuristic_fallback(self) -> None:
        with patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_PLANNER": "0"}, clear=False):
            result = self.planner.plan_task_actions(
                request_text="주간 운영회의를 요약해줘",
                task_input=self.task_input,
                metadata={},
                available_tools=[SUMMARY_TOOL],
                sensitivity="low",
                external_send=False,
                eligibility=[{"tool_id": "internal.summary.generate", "eligible": True, "reason": "always_required_summary"}],
            )

        self.assertEqual(result.source, "heuristic_fallback")
        self.assertTrue(result.degraded_mode)
        self.assertEqual([item.tool_id for item in result.actions], ["internal.summary.generate"])
        self.assertEqual(result.provider_selection["provider_id"], "local_lmstudio")
        self.assertEqual(result.eligible_tools[0]["tool_id"], "internal.summary.generate")

    def test_fallback_can_plan_summary_ticket_and_slack_when_requested(self) -> None:
        with patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_PLANNER": "0"}, clear=False):
            result = self.planner.plan_task_actions(
                request_text="운영회의를 요약하고 후속 티켓을 만들고 슬랙으로 공유해줘",
                task_input=self.task_input,
                metadata={"notify_channel": "#ops-alerts", "ticket_project_id": "OPS", "create_ticket": True},
                available_tools=[SUMMARY_TOOL, TICKET_TOOL, SLACK_TOOL],
                sensitivity="low",
                external_send=False,
                eligibility=[
                    {"tool_id": "internal.summary.generate", "eligible": True, "reason": "always_required_summary"},
                    {"tool_id": "redmine.issue.create", "eligible": True, "reason": "ticket_project_available_and_intent_detected"},
                    {"tool_id": "slack.message.send", "eligible": True, "reason": "notify_channel_available"},
                ],
                default_notify_channel="#ops-alerts",
            )

        self.assertEqual(
            [item.tool_id for item in result.actions],
            ["internal.summary.generate", "redmine.issue.create", "slack.message.send"],
        )
        self.assertEqual(result.actions[2].payload_overrides["channel"], "#ops-alerts")

    def test_live_planner_uses_llm_result_when_response_is_valid(self) -> None:
        with (
            patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_PLANNER": "1"}, clear=False),
            patch("app.agent_planner._detect_openai_compatible_model", return_value="lmstudio-loaded-model"),
            patch(
                "app.agent_planner._call_planner_openai_compatible_chat",
                return_value=(
                    '{"actions":['
                    '{"tool_id":"internal.summary.generate","reason":"summary first"},'
                    '{"tool_id":"redmine.issue.create","reason":"open a follow-up ticket"},'
                    '{"tool_id":"slack.message.send","reason":"notify team","payload_overrides":{"channel":"#ops-alerts"}}'
                    '],"confidence":0.92,"rationale":"summary, ticket, notify"}'
                ),
            ),
        ):
            result = self.planner.plan_task_actions(
                request_text="운영회의를 요약하고 후속 티켓을 만들고 슬랙으로 공유해줘",
                task_input=self.task_input,
                metadata={"notify_channel": "#ops-alerts", "ticket_project_id": "OPS"},
                available_tools=[SUMMARY_TOOL, TICKET_TOOL, SLACK_TOOL],
                sensitivity="low",
                external_send=False,
                eligibility=[
                    {"tool_id": "internal.summary.generate", "eligible": True, "reason": "always_required_summary"},
                    {"tool_id": "redmine.issue.create", "eligible": True, "reason": "ticket_project_available_and_intent_detected"},
                    {"tool_id": "slack.message.send", "eligible": True, "reason": "notify_channel_available"},
                ],
                default_notify_channel="#ops-alerts",
            )

        self.assertEqual(result.source, "llm")
        self.assertFalse(result.degraded_mode)
        self.assertEqual(
            [item.tool_id for item in result.actions],
            ["internal.summary.generate", "redmine.issue.create", "slack.message.send"],
        )
        self.assertAlmostEqual(float(result.confidence or 0), 0.92, places=2)
        self.assertEqual(result.provider_selection["provider_id"], "local_lmstudio")
        self.assertEqual(result.provider_selection["model"], "lmstudio-loaded-model")
        self.assertEqual(result.eligible_tools[1]["tool_id"], "redmine.issue.create")

    def test_live_planner_falls_back_when_response_is_invalid(self) -> None:
        with (
            patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_PLANNER": "1"}, clear=False),
            patch("app.agent_planner._detect_openai_compatible_model", return_value="lmstudio-loaded-model"),
            patch("app.agent_planner._call_planner_openai_compatible_chat", return_value='{"actions":[{"tool_id":"slack.message.send"}]}'),
        ):
            result = self.planner.plan_task_actions(
                request_text="운영회의를 요약하고 후속 티켓을 만들고 슬랙으로 공유해줘",
                task_input=self.task_input,
                metadata={"notify_channel": "#ops-alerts", "ticket_project_id": "OPS"},
                available_tools=[SUMMARY_TOOL, TICKET_TOOL, SLACK_TOOL],
                sensitivity="low",
                external_send=False,
                eligibility=[
                    {"tool_id": "internal.summary.generate", "eligible": True, "reason": "always_required_summary"},
                    {"tool_id": "redmine.issue.create", "eligible": True, "reason": "ticket_project_available_and_intent_detected"},
                    {"tool_id": "slack.message.send", "eligible": True, "reason": "notify_channel_available"},
                ],
                default_notify_channel="#ops-alerts",
            )

        self.assertEqual(result.source, "llm_error_fallback")
        self.assertTrue(result.degraded_mode)
        self.assertIn("first action must", str(result.fallback_reason))
        self.assertEqual(
            [item.tool_id for item in result.actions],
            ["internal.summary.generate", "redmine.issue.create", "slack.message.send"],
        )

    def test_live_planner_falls_back_for_unsupported_provider(self) -> None:
        api_only_registry = ModelRegistry(
            version=1,
            providers=(
                ProviderConfig(
                    provider_id="api_only",
                    provider_type="api",
                    enabled=True,
                    engine="anthropic",
                    model="claude",
                    purpose="planning",
                ),
            ),
            routing_rules=(RoutingRule(when={"task_type": "plan_actions"}, use_provider="api_only"),),
        )
        planner = AgentPlanner(api_only_registry)
        with patch.dict(os.environ, {"NEWCLAW_ENABLE_LLM_PLANNER": "1"}, clear=False):
            result = planner.plan_task_actions(
                request_text="주간 운영회의를 요약해줘",
                task_input=self.task_input,
                metadata={},
                available_tools=[SUMMARY_TOOL],
                sensitivity="low",
                external_send=False,
                eligibility=[{"tool_id": "internal.summary.generate", "eligible": True, "reason": "always_required_summary"}],
            )

        self.assertEqual(result.source, "heuristic_fallback")
        self.assertEqual(result.fallback_reason, "unsupported_provider")


if __name__ == "__main__":
    unittest.main()
