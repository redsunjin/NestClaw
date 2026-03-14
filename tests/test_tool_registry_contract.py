from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.tool_registry import (
    compact_overlay_tool_registry,
    get_tool_capability,
    list_tool_capabilities,
    load_tool_registry,
    remove_tool_registry_tool,
    upsert_tool_registry_tool,
    validate_tool_capability,
)


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

    def test_upsert_tool_registry_tool_writes_overlay_registry(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            overlay_path = Path(tmp_dir) / "tool_registry_runtime.yaml"
            capability = upsert_tool_registry_tool(
                overlay_path,
                {
                    "tool_id": "slack.message.contract_test",
                    "title": "Contract Test Slack Tool",
                    "description": "test tool",
                    "adapter": "slack_api",
                    "method": "message.send",
                    "action_type": "slack_message_contract_test",
                    "external_system": "slack",
                    "capability_family": "messaging",
                    "default_risk_level": "medium",
                    "default_approval_required": False,
                    "supports_dry_run": True,
                    "required_payload_fields": ["channel", "text"],
                },
            )

            self.assertEqual(capability.tool_id, "slack.message.contract_test")
            overlay_registry = load_tool_registry(overlay_path, overlay_path=None)
            self.assertEqual(overlay_registry.tools[0].tool_id, "slack.message.contract_test")

    def test_validate_tool_capability_rejects_unknown_adapter(self) -> None:
        report = validate_tool_capability(
            {
                "tool_id": "custom.tool.invalid",
                "title": "Invalid Tool",
                "description": "bad adapter",
                "adapter": "unknown_adapter",
                "method": "run",
                "action_type": "custom_tool_invalid",
                "external_system": "custom",
                "capability_family": "general",
                "default_risk_level": "medium",
                "default_approval_required": False,
                "supports_dry_run": True,
                "required_payload_fields": ["input"],
            }
        )
        self.assertFalse(report["valid"])
        failed_checks = {item["name"] for item in report["checks"] if item["status"] == "FAIL"}
        self.assertIn("adapter_known", failed_checks)

    def test_compact_and_remove_overlay_registry_tool(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir) / "tool_registry.yaml"
            overlay_path = Path(tmp_dir) / "tool_registry_runtime.yaml"

            base_tool = {
                "tool_id": "slack.message.base",
                "title": "Base Slack Tool",
                "description": "base tool",
                "adapter": "slack_api",
                "method": "message.send",
                "action_type": "slack_message_base",
                "external_system": "slack",
                "capability_family": "messaging",
                "default_risk_level": "medium",
                "default_approval_required": False,
                "supports_dry_run": True,
                "required_payload_fields": ["channel", "text"],
            }
            overlay_tool = {
                **base_tool,
                "tool_id": "slack.message.overlay_only",
                "title": "Overlay Slack Tool",
                "action_type": "slack_message_overlay_only",
            }

            upsert_tool_registry_tool(base_path, base_tool)
            upsert_tool_registry_tool(overlay_path, base_tool)
            upsert_tool_registry_tool(overlay_path, overlay_tool)

            compact_result = compact_overlay_tool_registry(base_path, overlay_path)
            self.assertEqual(compact_result["removed_count"], 1)

            overlay_registry = load_tool_registry(overlay_path, overlay_path=None)
            self.assertEqual([item.tool_id for item in overlay_registry.tools], ["slack.message.overlay_only"])
            self.assertTrue(remove_tool_registry_tool(overlay_path, "slack.message.overlay_only"))
            self.assertFalse(overlay_path.exists())


if __name__ == "__main__":
    unittest.main()
