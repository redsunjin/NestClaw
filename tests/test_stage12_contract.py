import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from app.tool_registry import load_tool_registry


class TestStage12Contract(unittest.TestCase):
    def test_stage12_positioning_docs_exist(self) -> None:
        positioning = Path("NESTCLAW_PRODUCT_POSITIONING.md").read_text(encoding="utf-8")
        local_control = Path("NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md").read_text(encoding="utf-8")
        roadmap = Path("NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md").read_text(
            encoding="utf-8"
        )
        work_groups = Path("NEXT_WORK_GROUPS_2026-04-27_STAGE12.md").read_text(encoding="utf-8")
        poc = Path("NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md").read_text(encoding="utf-8")
        scheduler = Path("NESTCLAW_STAGE12_SCHEDULER_INVOCATION_GUIDE_2026-04-28.md").read_text(
            encoding="utf-8"
        )
        harness = Path("NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("local-first LLM job control plane", positioning)
        self.assertIn("cloud/API LLM", positioning)
        self.assertIn("Agent Profile", local_control)
        self.assertIn("Job Template", local_control)
        self.assertIn("Capability Pack", local_control)
        self.assertIn("Execution Budget", local_control)
        self.assertIn("Schedule Trigger", local_control)
        self.assertIn("newclaw job run", local_control)
        self.assertIn("Local Job Invocation PoC", poc)
        self.assertIn("daily_status_digest", poc)
        self.assertIn("readiness_check", poc)
        self.assertIn("newclaw job list", poc)
        self.assertIn("newclaw job describe", poc)
        self.assertIn("agent.bundle", poc)
        self.assertIn("HTTP", poc)
        self.assertIn("MCP", poc)
        self.assertIn("Stage 12 Scheduler Invocation Guide", scheduler)
        self.assertIn("scripts/run_stage12_scheduled_job.sh", scheduler)
        self.assertIn("cron", scheduler)
        self.assertIn("launchd", scheduler)
        self.assertIn("GitHub Actions", scheduler)
        self.assertIn("idempotency_key", scheduler)
        self.assertIn("Template Idempotency Policy", scheduler)
        self.assertIn("duplicate-policy", scheduler)
        self.assertIn("LLM Harness Configuration Guide", harness)
        self.assertIn("Provider Harness", harness)
        self.assertIn("Agent Profile Harness", harness)
        self.assertIn("Job Template Harness", harness)
        self.assertIn("Capability Pack Harness", harness)
        self.assertIn("Invocation Harness", harness)
        self.assertIn("QA Harness", harness)
        self.assertIn("configs/model_registry.yaml", harness)
        self.assertIn("configs/agent_profiles.json", harness)
        self.assertIn("configs/job_templates.json", harness)
        self.assertIn("configs/capability_packs.json", harness)
        self.assertIn("scripts/run_stage12_scheduled_job.sh", harness)
        self.assertIn("scripts/run_dev_qa_cycle.sh", harness)
        self.assertIn("scripts/validate_stage12_llm_harness.py", harness)
        self.assertIn("Stage 12 Priority Campaign", roadmap)
        self.assertIn("stage12-priority-campaign", work_groups)
        self.assertIn("stage12-job-surface-campaign", work_groups)
        self.assertIn("stage12-agent-facing-job-api-campaign", work_groups)
        self.assertIn("stage12-job-execution-hardening-campaign", work_groups)
        self.assertIn("stage12-job-history-dashboard-campaign", work_groups)
        self.assertIn("stage12-scheduler-invocation-campaign", work_groups)
        self.assertIn("stage12-scheduler-dedupe-campaign", work_groups)
        self.assertIn("stage12-llm-harness-configuration-campaign", work_groups)
        self.assertIn("stage12-llm-harness-validator-campaign", work_groups)
        self.assertIn("stage12-llm-harness-negative-fixtures-campaign", work_groups)
        self.assertIn("stage12-job-idempotency-examples-campaign", work_groups)

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

    def test_job_template_spec_and_sample_registry_exist(self) -> None:
        spec = Path("NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md").read_text(encoding="utf-8")
        jobs = json.loads(Path("configs/job_templates.json").read_text(encoding="utf-8"))
        profiles = json.loads(Path("configs/agent_profiles.json").read_text(encoding="utf-8"))
        profile_by_id = {profile["profile_id"]: profile for profile in profiles["profiles"]}

        self.assertIn("Job Template is the Stage 12 contract", spec)
        self.assertIn("input_schema", spec)
        self.assertIn("provider_policy", spec)
        self.assertIn("schedule_trigger", spec)
        self.assertIn("idempotency_key_policy", spec)
        self.assertIn("output_evidence", spec)
        self.assertEqual(jobs["version"], 1)

        templates = jobs["templates"]
        self.assertEqual(
            {template["template_id"] for template in templates},
            {"daily_status_digest", "issue_triage", "readiness_check"},
        )

        required_fields = {
            "template_id",
            "workflow_family",
            "submit_contract",
            "input_schema",
            "allowed_profile_ids",
            "required_capability_packs",
            "provider_policy",
            "schedule_trigger",
            "execution_budget_override",
            "approval_requirements",
            "output_evidence",
        }
        for template in templates:
            self.assertTrue(required_fields.issubset(template))
            self.assertEqual(template["submit_contract"]["surface"], "agent.submit")
            self.assertEqual(template["submit_contract"]["status_surface"], "agent.status")
            self.assertEqual(template["submit_contract"]["events_surface"], "agent.events")
            self.assertEqual(template["submit_contract"]["report_surface"], "agent.report")
            self.assertTrue(template["input_schema"]["required_fields"])
            self.assertIn("sensitivity", template["input_schema"]["required_fields"])
            self.assertFalse(template["input_schema"]["freeform_context_allowed"])
            self.assertTrue(template["allowed_profile_ids"])
            self.assertTrue(template["required_capability_packs"])
            self.assertNotIn("*", template["required_capability_packs"])
            self.assertEqual(template["schedule_trigger"]["invocation_surface"], "agent.submit")
            schedule = template["schedule_trigger"]
            idempotency_fields = set(schedule["idempotency_key_fields"])
            self.assertIn("template_id", idempotency_fields)
            self.assertIn("idempotency_key_policy", schedule)
            idempotency_policy = schedule["idempotency_key_policy"]
            self.assertEqual(
                set(re.findall(r"\{([^{}]+)\}", idempotency_policy["format"])),
                idempotency_fields,
            )
            self.assertTrue(idempotency_policy["format"].startswith("stage12:"))
            self.assertTrue(idempotency_policy["examples"])
            self.assertIn(idempotency_policy["recommended_duplicate_policy"], {"run", "skip", "fail"})
            self.assertIn("rerun_guidance", idempotency_policy)
            for key_example in idempotency_policy["examples"]:
                self.assertTrue(key_example.startswith("stage12:"))
                self.assertNotIn("{", key_example)
                self.assertNotIn("}", key_example)
                self.assertNotIn("local_ops_default", key_example)
            self.assertIn("task_id", template["output_evidence"]["audit_fields"])
            self.assertIn("template_id", template["output_evidence"]["audit_fields"])
            self.assertIn("profile_id", template["output_evidence"]["audit_fields"])

            for profile_id in template["allowed_profile_ids"]:
                self.assertIn(profile_id, profile_by_id)
                self.assertIn(template["template_id"], profile_by_id[profile_id]["allowed_job_templates"])

        issue_triage = next(template for template in templates if template["template_id"] == "issue_triage")
        self.assertTrue(issue_triage["provider_policy"]["local_first"])
        self.assertIn("cloud_api_llm", issue_triage["provider_policy"]["allowed_provider_classes"])
        self.assertEqual(issue_triage["provider_policy"]["external_send_policy"], "approval_required")

        readiness = next(template for template in templates if template["template_id"] == "readiness_check")
        self.assertEqual(readiness["provider_policy"]["fallback_profile_id"], "deterministic_fallback_default")
        self.assertIn("deterministic_fallback", readiness["provider_policy"]["allowed_provider_classes"])

        expected_examples = {
            "daily_status_digest": "stage12:daily_status_digest:daily:2026-04-28:ops_team",
            "issue_triage": "stage12:issue_triage:issue:redmine:NC-1024:2026-04-28T09",
            "readiness_check": "stage12:readiness_check:readiness:stage12-scheduler-smoke:stage12:local:2026-04-28",
        }
        expected_duplicate_policies = {
            "daily_status_digest": "skip",
            "issue_triage": "fail",
            "readiness_check": "skip",
        }
        for template in templates:
            policy = template["schedule_trigger"]["idempotency_key_policy"]
            self.assertIn(expected_examples[template["template_id"]], policy["examples"])
            self.assertEqual(policy["recommended_duplicate_policy"], expected_duplicate_policies[template["template_id"]])

    def test_capability_pack_spec_and_registry_bind_profiles_jobs_and_tools(self) -> None:
        spec = Path("NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md").read_text(encoding="utf-8")
        packs = json.loads(Path("configs/capability_packs.json").read_text(encoding="utf-8"))
        profiles = json.loads(Path("configs/agent_profiles.json").read_text(encoding="utf-8"))
        jobs = json.loads(Path("configs/job_templates.json").read_text(encoding="utf-8"))
        tool_registry = load_tool_registry(overlay_path=None)

        self.assertIn("Capability Pack is the Stage 12 allowlist boundary", spec)
        self.assertIn("allowed_tool_ids", spec)
        self.assertIn("denied_tool_ids", spec)
        self.assertIn("approval_requirements", spec)
        self.assertIn("data_boundary", spec)
        self.assertEqual(packs["version"], 1)

        profile_by_id = {profile["profile_id"]: profile for profile in profiles["profiles"]}
        template_by_id = {template["template_id"]: template for template in jobs["templates"]}
        pack_by_id = {pack["pack_id"]: pack for pack in packs["packs"]}
        tool_ids = {tool.tool_id for tool in tool_registry.tools}

        referenced_pack_ids = {
            pack_id
            for profile in profile_by_id.values()
            for pack_id in profile["allowed_capability_packs"]
        } | {
            pack_id
            for template in template_by_id.values()
            for pack_id in template["required_capability_packs"]
        }
        self.assertTrue(referenced_pack_ids.issubset(pack_by_id))

        required_fields = {
            "pack_id",
            "pack_type",
            "risk_level",
            "allowed_tool_ids",
            "denied_tool_ids",
            "runtime_read_surfaces",
            "approval_requirements",
            "data_boundary",
            "allowed_profile_ids",
            "allowed_template_ids",
            "audit_fields",
        }
        for pack in packs["packs"]:
            self.assertTrue(required_fields.issubset(pack))
            self.assertIn(pack["pack_type"], {"tool_allowlist", "runtime_readonly", "draft_ops"})
            self.assertIn(pack["risk_level"], {"low", "medium", "high", "critical"})
            self.assertNotIn("*", pack["allowed_tool_ids"])
            self.assertNotIn("*", pack["denied_tool_ids"])
            self.assertTrue(set(pack["allowed_tool_ids"]).issubset(tool_ids))
            self.assertTrue(set(pack["denied_tool_ids"]).issubset(tool_ids))
            self.assertTrue(pack["runtime_read_surfaces"] or pack["allowed_tool_ids"])
            self.assertIn("tool_write", pack["approval_requirements"])
            self.assertIn("external_send", pack["approval_requirements"])
            self.assertIn("external_send_policy", pack["data_boundary"])
            self.assertIn("task_id", pack["audit_fields"])
            self.assertIn("pack_id", pack["audit_fields"])
            for profile_id in pack["allowed_profile_ids"]:
                self.assertIn(profile_id, profile_by_id)
                self.assertIn(pack["pack_id"], profile_by_id[profile_id]["allowed_capability_packs"])
            for template_id in pack["allowed_template_ids"]:
                self.assertIn(template_id, template_by_id)

        for template in template_by_id.values():
            for pack_id in template["required_capability_packs"]:
                pack = pack_by_id[pack_id]
                self.assertIn(template["template_id"], pack["allowed_template_ids"])
                for profile_id in template["allowed_profile_ids"]:
                    self.assertIn(pack_id, profile_by_id[profile_id]["allowed_capability_packs"])

        ticket_pack = pack_by_id["ticket_draft_ops"]
        self.assertEqual(ticket_pack["approval_requirements"]["tool_write"], "approver_required")
        self.assertTrue(ticket_pack["approval_requirements"]["dry_run_required"])
        self.assertIn("redmine.issue.create", ticket_pack["allowed_tool_ids"])

        core_status = pack_by_id["core_status_readonly"]
        self.assertEqual(core_status["allowed_tool_ids"], [])
        self.assertIn("agent.status", core_status["runtime_read_surfaces"])

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
        self.assertEqual(data["items"][1]["unit_id"], "stage12-w1-002")
        self.assertIn(data["items"][1]["status"], {"in_progress", "completed"})
        self.assertEqual(data["items"][2]["unit_id"], "stage12-w1-003")
        self.assertIn(data["items"][2]["status"], {"in_progress", "completed"})
        self.assertEqual(data["items"][3]["unit_id"], "stage12-w1-004")
        self.assertIn(data["items"][3]["status"], {"in_progress", "completed"})

    def test_stage12_job_surface_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-job-surface-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-job-surface-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-job-discovery-surface",
                "g2-readiness-check-adapter",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w2-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})
        self.assertEqual(data["items"][1]["unit_id"], "stage12-w2-002")
        self.assertIn(data["items"][1]["status"], {"pending", "in_progress", "completed"})

    def test_stage12_agent_facing_job_api_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-agent-facing-job-api-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-agent-facing-job-api-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-http-job-api",
                "g2-mcp-job-tools",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w3-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})
        self.assertEqual(data["items"][1]["unit_id"], "stage12-w3-002")
        self.assertIn(data["items"][1]["status"], {"pending", "in_progress", "completed"})

    def test_stage12_job_execution_hardening_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-job-execution-hardening-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-job-execution-hardening-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-issue-triage-adapter-budget-guard",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w4-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_job_history_dashboard_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-job-history-dashboard-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-job-history-dashboard-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-job-run-history-dashboard",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w5-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_scheduler_invocation_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-scheduler-invocation-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-scheduler-invocation-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-scheduler-invocation-wrapper",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w6-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_scheduler_dedupe_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-scheduler-dedupe-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-scheduler-dedupe-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-scheduled-job-idempotency",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w7-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_llm_harness_configuration_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-llm-harness-configuration-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-llm-harness-configuration-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-llm-harness-configuration-guide",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w8-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_llm_harness_validator_campaign_exists(self) -> None:
        data = json.loads(
            Path("work/priority_campaigns/stage12-llm-harness-validator-campaign/campaign.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["campaign_id"], "stage12-llm-harness-validator-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-llm-harness-policy-validator",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w9-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_llm_harness_negative_fixtures_campaign_exists(self) -> None:
        data = json.loads(
            Path(
                "work/priority_campaigns/stage12-llm-harness-negative-fixtures-campaign/campaign.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(data["campaign_id"], "stage12-llm-harness-negative-fixtures-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-llm-harness-negative-validator-fixtures",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w10-001")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_job_idempotency_examples_campaign_exists(self) -> None:
        data = json.loads(
            Path(
                "work/priority_campaigns/stage12-job-idempotency-examples-campaign/campaign.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(data["campaign_id"], "stage12-job-idempotency-examples-campaign")
        self.assertEqual(data["target_stage"], 12)
        self.assertEqual(
            [item["item_id"] for item in data["items"]],
            [
                "g1-job-template-idempotency-examples",
            ],
        )
        self.assertEqual(data["items"][0]["unit_id"], "stage12-w10-002")
        self.assertIn(data["items"][0]["status"], {"in_progress", "completed"})

    def test_stage12_llm_harness_validator_rejects_negative_fixtures(self) -> None:
        fixture_dir = Path("tests/fixtures/stage12_llm_harness_negative")
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_stage12_llm_harness.py",
                "--agent-profiles",
                str(fixture_dir / "agent_profiles.json"),
                "--job-templates",
                str(fixture_dir / "job_templates.json"),
                "--capability-packs",
                str(fixture_dir / "capability_packs.json"),
                "--model-registry",
                str(fixture_dir / "model_registry.yaml"),
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertGreaterEqual(payload["counts"]["errors"], 12)
        errors = "\n".join(payload["errors"])
        expected_errors = [
            "profile local_bad_boundary: local_llm provider must use local provider type, got api",
            "profile local_bad_boundary: local_llm external_send_policy must be deny",
            "profile local_bad_boundary: local_llm execution_budget.allow_network must be false",
            "profile cloud_bad_sensitivity: cloud_api_llm provider must use api/cloud provider type, got local",
            "profile cloud_bad_sensitivity: cloud_api_llm allows unsafe sensitivity sensitive_internal",
            "job unsafe_scheduled_job: required_fields must include sensitivity field sensitivity",
            "job unsafe_scheduled_job: freeform_context_allowed must be false unless separately reviewed",
            "job unsafe_scheduled_job: default_profile_id must be allowed by template",
            "job unsafe_scheduled_job: provider class cloud_api_llm not allowed by provider_policy",
            "job unsafe_scheduled_job: scheduled jobs must include template_id in idempotency_key_fields",
            "pack unsafe_pack: wildcard tool ids are not allowed",
            "pack unsafe_pack: tools cannot be both allowed and denied",
            "model_registry: routing rule 0 uses unknown provider missing_provider",
        ]
        for expected in expected_errors:
            self.assertIn(expected, errors)

    def test_cycle_scripts_support_stage12(self) -> None:
        cycle_source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        auto_source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        poc_script = Path("scripts/run_stage12_local_job_poc.sh").read_text(encoding="utf-8")
        scheduler_script = Path("scripts/run_stage12_scheduled_job.sh").read_text(encoding="utf-8")
        scheduler_smoke = Path("scripts/run_stage12_scheduler_smoke.sh").read_text(encoding="utf-8")
        scheduler_dedupe = Path("scripts/run_stage12_scheduler_dedupe_smoke.sh").read_text(encoding="utf-8")
        validator_source = Path("scripts/validate_stage12_llm_harness.py").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..12", cycle_source)
        self.assertIn("check_stage_12", cycle_source)
        self.assertIn("tests.test_stage12_contract", cycle_source)
        self.assertIn("validate_stage12_llm_harness.py", cycle_source)
        self.assertIn("tests.test_stage12_job_invocation_smoke", cycle_source)
        self.assertIn("scripts/run_stage12_local_job_poc.sh", cycle_source)
        self.assertIn("scripts/run_stage12_scheduler_smoke.sh", cycle_source)
        self.assertIn("scripts/run_stage12_scheduler_dedupe_smoke.sh", cycle_source)
        self.assertIn("NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS", cycle_source)
        self.assertIn("run_with_timeout.py", cycle_source)
        self.assertIn("run_check_command", cycle_source)
        self.assertIn("app.cli job list", poc_script)
        self.assertIn("app.cli job describe", poc_script)
        self.assertIn("app.cli job run", poc_script)
        self.assertIn("app.cli job history", poc_script)
        self.assertIn("--template daily_status_digest", poc_script)
        self.assertIn("--template readiness_check", poc_script)
        self.assertIn("--template issue_triage", poc_script)
        self.assertIn("--include-handoff", poc_script)
        self.assertIn("app.cli job run", scheduler_script)
        self.assertIn("app.cli job history", scheduler_script)
        self.assertIn("--expect-status", scheduler_script)
        self.assertIn("summary.json", scheduler_script)
        self.assertIn("reports/stage12-scheduled-runs", scheduler_script)
        self.assertIn("--idempotency-key", scheduler_script)
        self.assertIn("--duplicate-policy", scheduler_script)
        self.assertIn("SKIPPED_DUPLICATE", scheduler_script)
        self.assertIn("examples/stage12_scheduler/readiness-input.json", scheduler_smoke)
        self.assertIn("stage12:readiness_check:readiness:stage12-scheduler-smoke", scheduler_smoke)
        self.assertIn("--duplicate-policy skip", scheduler_dedupe)
        self.assertIn("stage12-dedupe-smoke", scheduler_dedupe)
        self.assertIn("stage12.llm_harness_validator", validator_source)
        self.assertIn("cloud_api_llm", validator_source)
        self.assertIn("local_llm", validator_source)
        self.assertIn("idempotency_key_fields", validator_source)
        self.assertIn("idempotency_key_policy", validator_source)
        self.assertIn("external_send_policy must be deny", validator_source)
        self.assertTrue(Path("examples/stage12_scheduler/cron.example").is_file())
        self.assertTrue(Path("examples/stage12_scheduler/launchd.local.example.plist").is_file())
        self.assertTrue(Path("examples/stage12_scheduler/github-actions.example.yml").is_file())
        self.assertTrue(Path("examples/stage12_scheduler/issue-triage-input.json").is_file())
        self.assertTrue(Path("examples/stage12_scheduler/idempotency-policy.md").is_file())
        self.assertIn("target-stage:1..12", auto_source)
        self.assertIn("target-stage must be 1..12", auto_source)

    def test_capability_manifest_mentions_stage12_concepts(self) -> None:
        source = Path("NESTCLAW_CAPABILITY_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("agent_profile", source)
        self.assertIn("job_template", source)
        self.assertIn("capability_pack", source)
        self.assertIn("execution_budget", source)
        self.assertIn("schedule_trigger", source)
        self.assertIn("job_invocation", source)
        self.assertIn("job_discovery", source)
        self.assertIn("newclaw job list", source)
        self.assertIn("newclaw job describe", source)
        self.assertIn("newclaw job run", source)
        self.assertIn("scheduled_job_wrapper", source)
        self.assertIn("scheduled_job_dedupe", source)
        self.assertIn("scheduled_job_idempotency_policy", source)
        self.assertIn("llm_harness_configuration", source)
        self.assertIn("llm_harness_validator", source)
        self.assertIn("idempotency_key", source)
        self.assertIn("scripts/validate_stage12_llm_harness.py", source)
        self.assertIn("scripts/run_stage12_scheduled_job.sh", source)
        self.assertIn("NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md", source)

    def test_stage12_job_run_cli_surface_exists(self) -> None:
        cli_source = Path("app/cli.py").read_text(encoding="utf-8")
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        mcp_source = Path("app/mcp_server.py").read_text(encoding="utf-8")
        job_source = Path("app/stage12_jobs.py").read_text(encoding="utf-8")
        self.assertIn('subparsers.add_parser("job"', cli_source)
        self.assertIn('job_subparsers.add_parser("list"', cli_source)
        self.assertIn('job_subparsers.add_parser("describe"', cli_source)
        self.assertIn('job_subparsers.add_parser("run"', cli_source)
        self.assertIn('job_subparsers.add_parser("history"', cli_source)
        self.assertIn("stage12_job_list_payload", cli_source)
        self.assertIn("stage12_job_describe_payload", cli_source)
        self.assertIn("_job_run_payload", cli_source)
        self.assertIn("_job_history_payload", cli_source)
        self.assertIn("run_stage12_job", cli_source)
        self.assertIn("--idempotency-key", cli_source)
        self.assertIn("@APP.get(\"/api/v1/jobs\")", main_source)
        self.assertIn("@APP.get(\"/api/v1/jobs/runs\")", main_source)
        self.assertIn("@APP.get(\"/api/v1/jobs/{template_id}\")", main_source)
        self.assertIn("@APP.post(\"/api/v1/jobs/run\"", main_source)
        self.assertIn('"job.list"', mcp_source)
        self.assertIn('"job.describe"', mcp_source)
        self.assertIn('"job.run"', mcp_source)
        self.assertIn('"job.history"', mcp_source)
        self.assertIn("idempotency_key", mcp_source)
        self.assertIn("def run_stage12_job(", job_source)
        self.assertIn("def job_input_fingerprint(", job_source)
        self.assertIn("def default_job_idempotency_key(", job_source)
        self.assertIn("def job_list_payload(", job_source)
        self.assertIn("def job_describe_payload(", job_source)
        self.assertIn("daily_status_digest", cli_source)
        self.assertIn("readiness_check", cli_source)
        self.assertIn("issue_triage", job_source)
        self.assertIn("budget_enforcement", job_source)
        self.assertIn("input_fingerprint", job_source)
        self.assertIn("idempotency_key", job_source)
        self.assertIn("validate_execution_budget_policy", job_source)
        self.assertIn("agent.bundle", cli_source)
        self.assertIn("def job_run_history(", Path("app/services/orchestration_service.py").read_text(encoding="utf-8"))

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
