import json
import unittest
from pathlib import Path


class TestStage10Contract(unittest.TestCase):
    def test_stage10_work_groups_doc_exists(self) -> None:
        source = Path("NEXT_WORK_GROUPS_2026-04-05.md").read_text(encoding="utf-8")
        self.assertIn("stage10-priority-campaign", source)
        self.assertIn("Canonical Execution Bundle Export", source)
        self.assertIn("Role-Gated Operator Surface Hardening", source)
        self.assertIn("Readiness / Error Taxonomy Normalization", source)
        self.assertIn("MCP Transport / Deployment Hardening", source)

    def test_mcp_transport_guide_exists(self) -> None:
        source = Path("NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("stdio", source)
        self.assertIn("future boundary", source)
        self.assertIn("actor_id", source)
        self.assertIn("approval.approve", source)

    def test_stage10_priority_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage10-priority-campaign/campaign.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["campaign_id"], "stage10-priority-campaign")
        self.assertEqual(data["target_stage"], 10)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-canonical-execution-bundle-export",
                "g2-role-gated-operator-surface-hardening",
                "g3-readiness-error-taxonomy-normalization",
                "g4-mcp-transport-deployment-hardening",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage10-w1-001")
        self.assertEqual(data["items"][0]["status"], "completed")
        self.assertEqual(data["items"][0]["completed_unit_id"], "stage10-w1-001")
        self.assertEqual(data["items"][1]["unit_id"], "stage10-w1-002")
        self.assertEqual(data["items"][1]["status"], "completed")
        self.assertEqual(data["items"][1]["completed_unit_id"], "stage10-w1-002")
        self.assertEqual(data["items"][2]["unit_id"], "stage10-w1-003")
        self.assertEqual(data["items"][2]["status"], "completed")
        self.assertEqual(data["items"][2]["completed_unit_id"], "stage10-w1-003")
        self.assertEqual(data["items"][3]["unit_id"], "stage10-w1-004")
        self.assertEqual(data["items"][3]["status"], "completed")
        self.assertEqual(data["items"][3]["completed_unit_id"], "stage10-w1-004")

    def test_stage10_first_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage10-w1-001/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage10-w1-001/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage10-w1-001/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage10-w1-001", work_unit)
        self.assertIn("status: `DONE`", work_unit)
        self.assertIn("execution bundle", work_unit)
        self.assertIn("approval snapshot", plan_notes)
        self.assertIn("HTTP, non-interactive CLI, MCP", plan_notes)
        self.assertIn("approval detail", review_notes)

    def test_stage10_second_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage10-w1-002/WORK_UNIT.md").read_text(encoding="utf-8")
        self.assertIn("stage10-w1-002", work_unit)
        self.assertIn("status: `DONE`", work_unit)
        self.assertIn("role-based visual and interaction gating", work_unit)

    def test_stage10_third_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage10-w1-003/WORK_UNIT.md").read_text(encoding="utf-8")
        self.assertIn("stage10-w1-003", work_unit)
        self.assertIn("status: `DONE`", work_unit)
        self.assertIn("blocked, degraded, approval-pending, and retryable failure reasons", work_unit)

    def test_stage10_fourth_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage10-w1-004/WORK_UNIT.md").read_text(encoding="utf-8")
        self.assertIn("stage10-w1-004", work_unit)
        self.assertIn("status: `DONE`", work_unit)
        self.assertIn("MCP startup, transport, and auth expectations", work_unit)

    def test_execution_bundle_surface_is_declared(self) -> None:
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        cli_source = Path("app/cli.py").read_text(encoding="utf-8")
        mcp_source = Path("app/mcp_server.py").read_text(encoding="utf-8")
        orchestration_source = Path("app/services/orchestration_service.py").read_text(encoding="utf-8")
        self.assertIn('"/api/v1/agent/bundle/{task_id}"', main_source)
        self.assertIn('subparsers.add_parser("bundle"', cli_source)
        self.assertIn('"agent.bundle"', mcp_source)
        self.assertIn("def agent_bundle(", orchestration_source)

    def test_cycle_scripts_support_stage10(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..12", cycle_source)
        self.assertIn("check_stage_10", cycle_source)
        self.assertIn("tests.test_stage10_contract", cycle_source)
        self.assertIn("tests.test_agent_entrypoint_smoke", cycle_source)
        self.assertIn("tests.test_tool_cli_smoke", cycle_source)
        self.assertIn("tests.test_mcp_server_smoke", cycle_source)
        self.assertIn("target-stage:1..12", auto_source)
        self.assertIn("target-stage must be 1..12", auto_source)

    def test_integration_docs_reference_mcp_stdio_boundary(self) -> None:
        readme_source = Path("README.md").read_text(encoding="utf-8")
        spec_source = Path("NESTCLAW_AGENT_INTEGRATION_SPEC.md").read_text(encoding="utf-8")
        examples_source = Path("NESTCLAW_INTEGRATION_EXAMPLES.md").read_text(encoding="utf-8")
        self.assertIn("NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md", readme_source)
        self.assertIn("canonical transport는 stdio baseline", readme_source)
        self.assertIn("MCP Transport Baseline", spec_source)
        self.assertIn("packaged remote transport는 아직 baseline이 아니다", spec_source)
        self.assertIn("stdio Bootstrap", examples_source)
        self.assertIn("child process", examples_source)


if __name__ == "__main__":
    unittest.main()
