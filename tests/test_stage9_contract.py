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
                "g2-incident-ai-reasoning",
                "g3-operator-action-transparency",
                "g4-pilot-readiness-pack",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage9-w1-001")

    def test_stage9_first_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage9-w1-001/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage9-w1-001/PLAN_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage9-w1-001", work_unit)
        self.assertIn("Extract a shared registry-based planner-executor loop", work_unit)
        self.assertIn("## AI-First Planner Design", plan_notes)
        self.assertIn("공통 helper", plan_notes)

    def test_cycle_scripts_support_stage9(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..9", cycle_source)
        self.assertIn("check_stage_9", cycle_source)
        self.assertIn("tests.test_stage9_contract", cycle_source)
        self.assertIn("tests.test_planner_executor_service", cycle_source)

        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage:1..9", auto_source)
        self.assertIn("target-stage must be 1..9", auto_source)

    def test_shared_planner_executor_helper_exists_and_is_used(self) -> None:
        helper_source = Path("app/services/planner_executor_service.py").read_text(encoding="utf-8")
        self.assertIn("def record_planning_snapshot", helper_source)
        self.assertIn("def emit_planning_events", helper_source)
        self.assertIn("def execute_planned_actions", helper_source)
        self.assertIn("def record_action_results", helper_source)

        main_source = Path("app/main.py").read_text(encoding="utf-8")
        self.assertIn("record_planning_snapshot(", main_source)
        self.assertIn("emit_planning_events(", main_source)
        self.assertIn("execute_planned_actions(", main_source)
        self.assertIn("record_action_results(", main_source)


if __name__ == "__main__":
    unittest.main()
