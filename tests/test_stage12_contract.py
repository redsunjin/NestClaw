import json
import unittest
from pathlib import Path


class TestStage12Contract(unittest.TestCase):
    def test_stage12_positioning_docs_exist(self) -> None:
        positioning = Path("NESTCLAW_PRODUCT_POSITIONING.md").read_text(encoding="utf-8")
        local_control = Path("NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md").read_text(encoding="utf-8")
        roadmap = Path("NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md").read_text(
            encoding="utf-8"
        )
        work_groups = Path("NEXT_WORK_GROUPS_2026-04-27_STAGE12.md").read_text(encoding="utf-8")
        self.assertIn("local-first LLM job control plane", positioning)
        self.assertIn("cloud/API LLM", positioning)
        self.assertIn("Agent Profile", local_control)
        self.assertIn("Job Template", local_control)
        self.assertIn("Capability Pack", local_control)
        self.assertIn("Execution Budget", local_control)
        self.assertIn("Schedule Trigger", local_control)
        self.assertIn("Stage 12 Priority Campaign", roadmap)
        self.assertIn("stage12-priority-campaign", work_groups)

    def test_agent_profile_spec_and_sample_registry_exist(self) -> None:
        spec = Path("NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md").read_text(encoding="utf-8")
        registry = json.loads(Path("configs/agent_profiles.json").read_text(encoding="utf-8"))

        self.assertIn("Agent Profile is the Stage 12 boundary object", spec)
        self.assertIn("local_llm", spec)
        self.assertIn("cloud_api_llm", spec)
        self.assertIn("upper_agent_wrapper", spec)
        self.assertIn("deterministic_fallback", spec)
        self.assertIn("execution_budget", spec)
        self.assertIn("sensitivity_boundary", spec)
        self.assertIn("approval_policy", spec)

        self.assertEqual(registry["version"], 1)
        profiles = registry["profiles"]
        required_fields = {
            "profile_id",
            "provider_id",
            "provider_class",
            "allowed_job_templates",
            "allowed_capability_packs",
            "execution_budget",
            "sensitivity_boundary",
            "approval_policy",
            "audit_level",
        }
        for profile in profiles:
            self.assertTrue(required_fields.issubset(profile))
            self.assertTrue(profile["allowed_job_templates"])
            self.assertTrue(profile["allowed_capability_packs"])
            self.assertGreaterEqual(profile["execution_budget"]["max_tool_calls"], 0)
            self.assertIn(profile["audit_level"], {"minimal", "full"})

        classes = {profile["provider_class"] for profile in profiles}
        self.assertTrue(
            {"local_llm", "cloud_api_llm", "upper_agent_wrapper", "deterministic_fallback"}.issubset(classes)
        )

        local_profile = next(profile for profile in profiles if profile["provider_class"] == "local_llm")
        self.assertIn("sensitive_internal", local_profile["sensitivity_boundary"]["allowed_sensitivity"])
        self.assertEqual(local_profile["sensitivity_boundary"]["external_send_policy"], "deny")

        cloud_profile = next(profile for profile in profiles if profile["provider_class"] == "cloud_api_llm")
        self.assertNotIn("sensitive_internal", cloud_profile["sensitivity_boundary"]["allowed_sensitivity"])
        self.assertEqual(cloud_profile["sensitivity_boundary"]["external_send_policy"], "approval_required")
        self.assertEqual(cloud_profile["approval_policy"]["external_send"], "approver_required")

    def test_stage12_priority_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-priority-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-priority-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-agent-profile-spec",
                "g2-job-template-spec",
                "g3-capability-pack-binding",
                "g4-local-job-invocation-poc",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w1-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_cycle_scripts_support_stage12(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..12", cycle_source)
        self.assertIn("check_stage_12", cycle_source)
        self.assertIn("tests.test_stage12_contract", cycle_source)
        self.assertIn("NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS", cycle_source)
        self.assertIn("run_with_timeout.py", cycle_source)
        self.assertIn("run_check_command", cycle_source)
        self.assertIn("target-stage:1..12", auto_source)
        self.assertIn("target-stage must be 1..12", auto_source)

    def test_capability_manifest_mentions_stage12_concepts(self) -> None:
        source = Path("NESTCLAW_CAPABILITY_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("agent_profile", source)
        self.assertIn("job_template", source)
        self.assertIn("capability_pack", source)
        self.assertIn("execution_budget", source)
        self.assertIn("schedule_trigger", source)

    def test_governance_guardrails_cover_provider_boundaries(self) -> None:
        source = Path("NESTCLAW_GOVERNANCE_GUARDRAILS.md").read_text(encoding="utf-8")
        self.assertIn("local LLM", source)
        self.assertIn("cloud/API", source)
        self.assertIn("sensitivity", source)
        self.assertIn("provider routing", source)

    def test_first_stage12_micro_unit_is_plan_gated(self) -> None:
        work_unit = Path("work/micro_units/stage12-w1-001/WORK_UNIT.md").read_text(encoding="utf-8")
        plan_notes = Path("work/micro_units/stage12-w1-001/PLAN_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("stage12-w1-001", work_unit)
        self.assertRegex(work_unit, r"status: `(REVIEW_PENDING|IMPLEMENT_PENDING|EVALUATE_PENDING|DONE)`")
        self.assertIn("- [x] Plan gate passed", work_unit)
        self.assertIn("Agent Profile", plan_notes)
        self.assertIn("local provider", plan_notes)
        self.assertIn("cloud/API provider", plan_notes)
        self.assertIn("execution budget", plan_notes.lower())


if __name__ == "__main__":
    unittest.main()
