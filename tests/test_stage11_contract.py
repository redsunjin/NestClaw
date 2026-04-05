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
        self.assertIn(data["items"][0]["status"], {"pending", "in_progress", "completed"})

    def test_cycle_scripts_support_stage11(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..11", cycle_source)
        self.assertIn("check_stage_11", cycle_source)
        self.assertIn("tests.test_stage11_contract", cycle_source)
        self.assertIn("target-stage:1..11", auto_source)
        self.assertIn("target-stage must be 1..11", auto_source)

    def test_stage11_first_micro_unit_is_initialized(self) -> None:
        work_unit = Path("work/micro_units/stage11-w1-001/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage11-w1-001/PLAN_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage11-w1-001", work_unit)
        self.assertIn("status: `REVIEW_PENDING`", work_unit)
        self.assertIn("external env", plan_notes.lower())


if __name__ == "__main__":
    unittest.main()
