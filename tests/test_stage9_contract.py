import json
import unittest
from pathlib import Path


class TestStage9Contract(unittest.TestCase):
    def test_stage9_work_groups_doc_exists(self) -> None:
        source = Path("NEXT_WORK_GROUPS_2026-03-17.md").read_text(encoding="utf-8")
        self.assertIn("stage9-priority-campaign", source)
        self.assertIn("Common Planner / Executor Convergence", source)
        self.assertIn("Incident AI Reasoning Expansion", source)
        self.assertIn("Operator Action Transparency", source)
        self.assertIn("Pilot Readiness Pack", source)
        self.assertIn("NEWCLAW_STAGE8_SANDBOX_ENABLED", source)
        self.assertIn("run_stage8_readiness_bundle.sh", source)

    def test_stage9_priority_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage9-priority-campaign/campaign.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["campaign_id"], "stage9-priority-campaign")
        self.assertEqual(data["target_stage"], 9)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-common-planner-executor-loop",
                "g1-provider-report-finalization",
                "g2-incident-ai-reasoning",
                "g3-operator-action-transparency",
                "g4-pilot-readiness-pack",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage9-w1-001")
        self.assertEqual(data["items"][0]["status"], "completed")
        self.assertEqual(data["items"][1]["unit_id"], "stage9-w1-002")
        self.assertEqual(data["items"][1]["status"], "completed")
        self.assertEqual(data["items"][1]["completed_unit_id"], "stage9-w1-002")
        self.assertEqual(data["items"][2]["unit_id"], "stage9-w1-003")
        self.assertEqual(data["items"][2]["status"], "completed")
        self.assertEqual(data["items"][2]["completed_unit_id"], "stage9-w1-003")
        self.assertEqual(data["items"][3]["unit_id"], "stage9-w1-004")
        self.assertEqual(data["items"][3]["status"], "completed")
        self.assertEqual(data["items"][3]["completed_unit_id"], "stage9-w1-004")
        self.assertEqual(data["items"][4]["unit_id"], "stage9-w1-005")
        self.assertEqual(data["items"][4]["status"], "completed")
        self.assertEqual(data["items"][4]["completed_unit_id"], "stage9-w1-005")

    def test_stage9_first_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage9-w1-001/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage9-w1-001/PLAN_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage9-w1-001", work_unit)
        self.assertIn("Extract a shared registry-based planner-executor loop", work_unit)
        self.assertIn("## AI-First Planner Design", plan_notes)
        self.assertIn("공통 helper", plan_notes)

    def test_stage9_second_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage9-w1-002/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage9-w1-002/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage9-w1-002/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage9-w1-002", work_unit)
        self.assertIn("provider-selection recording", work_unit)
        self.assertIn("report/result finalization", plan_notes)
        self.assertIn("planner_executor_service", review_notes)

    def test_stage9_third_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage9-w1-003/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage9-w1-003/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage9-w1-003/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage9-w1-003", work_unit)
        self.assertIn("incident AI planner baseline", work_unit)
        self.assertIn("deterministic fallback", plan_notes)
        self.assertIn("planner rationale", review_notes)

    def test_stage9_fourth_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage9-w1-004/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage9-w1-004/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage9-w1-004/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage9-w1-004", work_unit)
        self.assertIn("status: `DONE`", work_unit)
        self.assertIn("planner rationale, fallback state, and action sequencing", work_unit)
        self.assertIn("operator dashboard", plan_notes)
        self.assertIn("action rail", review_notes)

    def test_stage9_fifth_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage9-w1-005/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage9-w1-005/PLAN_NOTES.md").read_text(encoding="utf-8")
        review_notes = Path("work/micro_units/stage9-w1-005/REVIEW_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage9-w1-005", work_unit)
        self.assertIn("status: `DONE`", work_unit)
        self.assertIn("pilot evidence matrix, go-no-go packet", work_unit)
        self.assertIn("blocked-to-resume runbook", plan_notes)
        self.assertIn("readiness source", review_notes)

    def test_cycle_scripts_support_stage9(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..10", cycle_source)
        self.assertIn("check_stage_9", cycle_source)
        self.assertIn("check_stage_10", cycle_source)
        self.assertIn("tests.test_stage9_contract", cycle_source)
        self.assertIn("tests.test_stage10_contract", cycle_source)
        self.assertIn("tests.test_planner_executor_service", cycle_source)
        self.assertIn("tests.test_agent_planner_runtime", cycle_source)
        self.assertIn("tests.test_incident_runtime_smoke", cycle_source)

        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage:1..10", auto_source)
        self.assertIn("target-stage must be 1..10", auto_source)

    def test_shared_planner_executor_helper_exists_and_is_used(self) -> None:
        helper_source = Path("app/services/planner_executor_service.py").read_text(encoding="utf-8")
        self.assertIn("def record_planning_snapshot", helper_source)
        self.assertIn("def emit_planning_events", helper_source)
        self.assertIn("def execute_planned_actions", helper_source)
        self.assertIn("def record_action_results", helper_source)
        self.assertIn("def record_provider_selection", helper_source)
        self.assertIn("def write_report", helper_source)
        self.assertIn("def finalize_execution", helper_source)

        main_source = Path("app/main.py").read_text(encoding="utf-8")
        self.assertIn("record_planning_snapshot(", main_source)
        self.assertIn("emit_planning_events(", main_source)
        self.assertIn("execute_planned_actions(", main_source)
        self.assertIn("record_action_results(", main_source)
        self.assertIn("record_provider_selection(", main_source)
        self.assertIn("write_report(", main_source)
        self.assertIn("finalize_execution(", main_source)

    def test_operator_surfaces_expose_transparency_slots(self) -> None:
        console_html = Path("app/static/agent-console.html").read_text(encoding="utf-8")
        quickstart_html = Path("app/static/agent-quickstart.html").read_text(encoding="utf-8")
        orchestration_source = Path("app/services/orchestration_service.py").read_text(encoding="utf-8")
        self.assertIn("planner-signal-strip", console_html)
        self.assertIn("planner-rationale", console_html)
        self.assertIn("execution-detail", console_html)
        self.assertIn("quick-planner-signals", quickstart_html)
        self.assertIn("quick-action-rail", quickstart_html)
        self.assertIn("quick-execution-rail", quickstart_html)
        self.assertIn('"planning_rationale"', orchestration_source)
        self.assertIn('"run_mode"', orchestration_source)

    def test_pilot_packet_docs_exist_and_are_linked(self) -> None:
        readme_source = Path("README.md").read_text(encoding="utf-8")
        matrix_source = Path("NESTCLAW_PILOT_EVIDENCE_MATRIX_2026-04-05.md").read_text(encoding="utf-8")
        packet_source = Path("NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md").read_text(encoding="utf-8")
        runbook_source = Path("STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md").read_text(encoding="utf-8")
        self.assertIn("Pilot evidence matrix", readme_source)
        self.assertIn("Pilot go/no-go packet", readme_source)
        self.assertIn("blocked-to-resumed runbook", readme_source)
        self.assertIn("NO-GO", matrix_source)
        self.assertIn("BLOCKED", matrix_source)
        self.assertIn("NO-GO for external live pilot", packet_source)
        self.assertIn("Required Env Contract", runbook_source)
        self.assertIn("run_stage8_readiness_bundle.sh", runbook_source)


if __name__ == "__main__":
    unittest.main()
