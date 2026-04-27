import json
import unittest
from pathlib import Path


class TestStage11Contract(unittest.TestCase):
    def test_stage11_work_groups_doc_exists(self) -> None:
        source = Path("NEXT_WORK_GROUPS_2026-04-05_STAGE11.md").read_text(encoding="utf-8")
        self.assertIn("stage11-priority-campaign", source)
        self.assertIn("External Env Handoff Profile", source)
        self.assertIn("Operator Handoff Packet Export", source)
        self.assertIn("Deployment Profile Bootstrap", source)
        self.assertIn("Pilot Acceptance Cycle", source)

    def test_stage11_priority_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage11-priority-campaign/campaign.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["campaign_id"], "stage11-priority-campaign")
        self.assertEqual(data["target_stage"], 11)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-external-env-handoff-profile",
                "g2-operator-handoff-packet-export",
                "g3-deployment-profile-bootstrap",
                "g4-pilot-acceptance-cycle",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage11-w1-001")
        self.assertEqual(data["items"][0]["status"], "completed")
        self.assertEqual(data["items"][0]["completed_unit_id"], "stage11-w1-001")
        self.assertEqual(data["items"][1]["unit_id"], "stage11-w1-002")
        self.assertIn(data["items"][1]["status"], {"completed"})
        self.assertEqual(data["items"][2]["unit_id"], "stage11-w1-003")
        self.assertIn(data["items"][2]["status"], {"in_progress", "completed"})

    def test_cycle_scripts_support_stage11(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..12", cycle_source)
        self.assertIn("check_stage_11", cycle_source)
        self.assertIn("tests.test_stage11_contract", cycle_source)
        self.assertIn("tests.test_stage11_env_handoff_smoke", cycle_source)
        self.assertIn("tests.test_stage11_deployment_bootstrap_smoke", cycle_source)
        self.assertIn("tests.test_stage11_pilot_acceptance_smoke", cycle_source)
        self.assertIn("target-stage:1..12", auto_source)
        self.assertIn("target-stage must be 1..12", auto_source)

    def test_stage11_first_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage11-w1-001/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage11-w1-001/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage11-w1-001/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage11-w1-001", work_unit)
        self.assertRegex(work_unit, r"status: `(REVIEW_PENDING|IMPLEMENT_PENDING|EVALUATE_PENDING|DONE)`")
        self.assertIn("external env", plan_notes.lower())
        self.assertIn("secret", review_notes.lower())
        self.assertIn("blocked", review_notes.lower())

    def test_stage11_external_env_profile_exists(self) -> None:
        source = Path("STAGE8_EXTERNAL_ENV_HANDOFF_PROFILE_2026-04-05.md").read_text(encoding="utf-8")
        self.assertIn("NEWCLAW_STAGE8_SANDBOX_ENABLED", source)
        self.assertIn("NEWCLAW_REDMINE_MCP_ENDPOINT", source)
        self.assertIn("configs/stage8_external_env.handoff.env.example", source)
        self.assertIn("scripts/validate_stage8_env_handoff.sh", source)
        self.assertIn("BLOCKED", source)

    def test_stage11_env_template_exists(self) -> None:
        source = Path("configs/stage8_external_env.handoff.env.example").read_text(encoding="utf-8")
        self.assertIn("NEWCLAW_STAGE8_SANDBOX_ENABLED=", source)
        self.assertIn('NEWCLAW_STAGE8_SANDBOX_TRANSITION="In Progress"', source)
        self.assertIn("NEWCLAW_REDMINE_MCP_TOKEN=", source)

    def test_stage11_deployment_bootstrap_profile_exists(self) -> None:
        source = Path("NESTCLAW_DEPLOYMENT_BOOTSTRAP_PROFILES_2026-04-08.md").read_text(encoding="utf-8")
        profile_source = Path("configs/deployment_bootstrap_profiles.json").read_text(encoding="utf-8")
        self.assertIn("local_dev", source)
        self.assertIn("operator_sidecar", source)
        self.assertIn("upper_agent_host", source)
        self.assertIn("uvicorn app.main:APP", source)
        self.assertIn("python3 app/mcp_server.py", source)
        self.assertIn('"profile_id": "local_dev"', profile_source)
        self.assertIn('"profile_id": "upper_agent_host"', profile_source)

    def test_stage11_pilot_acceptance_cycle_exists(self) -> None:
        source = Path("NESTCLAW_PILOT_ACCEPTANCE_CYCLE_2026-04-10.md").read_text(encoding="utf-8")
        self.assertIn("GO", source)
        self.assertIn("Conditional Go", source)
        self.assertIn("NO-GO", source)
        self.assertIn("operational hold", source)
        self.assertIn("NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md", source)
        self.assertIn("STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md", source)

    def test_stage11_operator_handoff_packet_spec_and_surfaces_exist(self) -> None:
        spec_source = Path("NESTCLAW_OPERATOR_HANDOFF_PACKET_SPEC.md").read_text(encoding="utf-8")
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        cli_source = Path("app/cli.py").read_text(encoding="utf-8")
        mcp_source = Path("app/mcp_server.py").read_text(encoding="utf-8")
        self.assertIn("agent.handoff", spec_source)
        self.assertIn("packet_type", spec_source)
        self.assertIn('"/api/v1/agent/handoff/{task_id}"', main_source)
        self.assertIn('subparsers.add_parser("handoff"', cli_source)
        self.assertIn('"agent.handoff"', mcp_source)

    def test_stage11_second_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage11-w1-002/WORK_UNIT.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage11-w1-002/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage11-w1-002", work_unit)
        self.assertRegex(work_unit, r"status: `(REVIEW_PENDING|IMPLEMENT_PENDING|EVALUATE_PENDING|DONE)`")
        self.assertIn("handoff", review_notes.lower())
        self.assertIn("bundle", review_notes.lower())

    def test_stage11_third_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage11-w1-003/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage11-w1-003/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage11-w1-003/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage11-w1-003", work_unit)
        self.assertRegex(work_unit, r"status: `(REVIEW_PENDING|IMPLEMENT_PENDING|EVALUATE_PENDING|DONE)`")
        self.assertIn("deployment", plan_notes.lower())
        self.assertIn("uvicorn", plan_notes.lower())
        self.assertIn("trust boundary", review_notes.lower())

    def test_stage11_fourth_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage11-w1-004/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage11-w1-004/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage11-w1-004/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage11-w1-004", work_unit)
        self.assertRegex(work_unit, r"status: `(REVIEW_PENDING|IMPLEMENT_PENDING|EVALUATE_PENDING|DONE)`")
        self.assertIn("acceptance", plan_notes.lower())
        self.assertIn("operational hold", plan_notes.lower())
        self.assertIn("validator", review_notes.lower())


if __name__ == "__main__":
    unittest.main()
