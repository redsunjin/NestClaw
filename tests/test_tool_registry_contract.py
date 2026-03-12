from __future__ import annotations

import unittest
from pathlib import Path

from app.tool_registry import get_tool_capability, list_tool_capabilities, load_tool_registry


class TestToolRegistryContract(unittest.TestCase):
    def test_tool_registry_config_exists(self) -> None:
        self.assertTrue(Path("configs/tool_registry.yaml").is_file())

    def test_load_tool_registry_contains_redmine_create_capability(self) -> None:
        registry = load_tool_registry()
        capability = get_tool_capability(registry, "redmine.issue.create")

        self.assertEqual(capability.adapter, "redmine_mcp")
        self.assertEqual(capability.method, "issue.create")
        self.assertEqual(capability.action_type, "redmine_issue_create")
        self.assertEqual(capability.external_system, "redmine")
        self.assertEqual(capability.capability_family, "ticketing")
        self.assertIn("project_id", capability.required_payload_fields)
        self.assertTrue(capability.supports_dry_run)

    def test_load_tool_registry_contains_internal_summary_capability(self) -> None:
        registry = load_tool_registry()
        capability = get_tool_capability(registry, "internal.summary.generate")

        self.assertEqual(capability.adapter, "provider_invoker")
        self.assertEqual(capability.method, "summary.generate")
        self.assertEqual(capability.external_system, "internal")
        self.assertEqual(capability.capability_family, "content_generation")
        self.assertIn("meeting_title", capability.required_payload_fields)
        self.assertFalse(capability.supports_dry_run)

    def test_load_tool_registry_contains_slack_capability(self) -> None:
        registry = load_tool_registry()
        capability = get_tool_capability(registry, "slack.message.send")

        self.assertEqual(capability.adapter, "slack_api")
        self.assertEqual(capability.method, "message.send")
        self.assertEqual(capability.external_system, "slack")
        self.assertEqual(capability.capability_family, "messaging")
        self.assertIn("channel", capability.required_payload_fields)
        self.assertTrue(capability.supports_dry_run)

    def test_list_tool_capabilities_supports_filters(self) -> None:
        registry = load_tool_registry()

        redmine_tools = list_tool_capabilities(registry, external_system="redmine")
        ticketing_tools = list_tool_capabilities(registry, capability_family="ticketing")
        internal_tools = list_tool_capabilities(registry, external_system="internal")

        self.assertGreaterEqual(len(redmine_tools), 5)
        self.assertEqual(len(redmine_tools), len(ticketing_tools))
        self.assertEqual([item.tool_id for item in internal_tools], ["internal.summary.generate"])


if __name__ == "__main__":
    unittest.main()
