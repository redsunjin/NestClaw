from __future__ import annotations

import unittest
from pathlib import Path


try:
    from app import cli as cli_module
    from app import main as main_module
    from tests.runtime_test_utils import reset_runtime_state
except Exception as exc:  # pragma: no cover - environment dependent
    cli_module = None
    main_module = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(cli_module is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestStage12JobInvocationSmoke(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)

    def _daily_status_input(self) -> dict[str, object]:
        return {
            "date": "2026-04-28",
            "audience": "ops_team",
            "sensitivity": "internal",
            "sources": [
                {
                    "name": "standup",
                    "status": "on_track",
                    "summary": "Stage 12 job runner contract is ready for a bounded PoC.",
                },
                {
                    "name": "qa",
                    "status": "watch",
                    "summary": "Local model availability is not required because fallback evidence is captured.",
                },
            ],
            "focus_areas": ["job invocation", "audit evidence"],
            "excluded_topics": ["cloud relay"],
        }

    def test_daily_status_digest_job_runs_and_captures_evidence(self) -> None:
        payload, exit_code = cli_module._job_run_payload(
            template_id="daily_status_digest",
            profile_id="local_ops_default",
            input_payload=self._daily_status_input(),
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
            include_bundle=True,
            include_handoff=True,
            max_chars=2400,
        )

        self.assertEqual(exit_code, 0, payload)
        invocation = payload["job_invocation"]
        self.assertEqual(invocation["template_id"], "daily_status_digest")
        self.assertEqual(invocation["profile_id"], "local_ops_default")
        self.assertEqual(invocation["provider_class"], "local_llm")
        self.assertEqual(invocation["capability_pack_ids"], ["internal_digest_basic"])
        self.assertEqual(invocation["runtime_surfaces"]["submit"], "agent.submit")
        self.assertEqual(invocation["runtime_surfaces"]["bundle"], "agent.bundle")
        self.assertEqual(invocation["runtime_surfaces"]["handoff"], "agent.handoff")

        status = payload["status"]
        self.assertEqual(status["resolved_kind"], "task")
        self.assertEqual(status["status"], "DONE")
        self.assertEqual(status["state_summary"]["canonical_state"], "done")
        self.assertIn(status["state_summary"]["canonical_reason_code"], {"completed", "planner_degraded"})
        self.assertTrue(status.get("planning_provenance"))
        self.assertTrue(status.get("provider_invocation"))
        self.assertEqual(status["result"]["actions_executed"], 1)

        report_path = Path(str(status["result"]["report_path"]))
        self.assertTrue(report_path.is_file())
        self.assertIn("Stage 12 job runner contract", report_path.read_text(encoding="utf-8"))

        event_types = {item["event_type"] for item in payload["events"]["items"]}
        self.assertIn("TASK_CREATED", event_types)
        self.assertIn("AGENT_ROUTED", event_types)
        self.assertIn("TASK_ACTIONS_PLANNED", event_types)
        self.assertIn("PLANNED_ACTION_EXECUTED", event_types)

        self.assertTrue(payload["report"]["available"])
        self.assertEqual(payload["bundle"]["bundle_version"], "v1")
        self.assertEqual(payload["bundle"]["status"]["task_id"], invocation["task_id"])
        self.assertEqual(payload["handoff"]["packet_type"], "completed")
        self.assertEqual(payload["handoff"]["bundle_ref"]["mcp"], "agent.bundle")

    def test_job_discovery_surfaces_describe_executable_templates(self) -> None:
        list_payload, list_exit_code = cli_module._job_list_payload()
        self.assertEqual(list_exit_code, 0, list_payload)
        by_id = {item["template_id"]: item for item in list_payload["items"]}
        self.assertTrue(by_id["daily_status_digest"]["executable"])
        self.assertTrue(by_id["readiness_check"]["executable"])
        self.assertFalse(by_id["issue_triage"]["executable"])
        self.assertIn("local_ops_default", by_id["readiness_check"]["compatible_profile_ids"])
        self.assertIn("readiness_check", list_payload["implemented_job_template_ids"])

        describe_payload, describe_exit_code = cli_module._job_describe_payload(
            template_id="readiness_check",
            profile_id="local_ops_default",
        )
        self.assertEqual(describe_exit_code, 0, describe_payload)
        self.assertEqual(describe_payload["template"]["template_id"], "readiness_check")
        self.assertEqual(
            describe_payload["template"]["required_capability_packs"],
            ["readiness_probe_readonly", "core_status_readonly"],
        )
        self.assertEqual(describe_payload["template"]["runtime_surfaces"]["submit"], "agent.submit")
        self.assertTrue(describe_payload["examples"])

    def test_readiness_check_job_runs_and_captures_evidence(self) -> None:
        payload, exit_code = cli_module._job_run_payload(
            template_id="readiness_check",
            profile_id="local_ops_default",
            input_payload={
                "check_set": "stage8-readiness",
                "target_stage": 8,
                "sensitivity": "internal",
                "env_profile": "local",
                "strict_gate": False,
                "timeout_seconds": 15,
            },
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
            include_bundle=True,
            include_handoff=True,
            max_chars=2400,
        )

        self.assertEqual(exit_code, 0, payload)
        invocation = payload["job_invocation"]
        self.assertEqual(invocation["template_id"], "readiness_check")
        self.assertEqual(invocation["profile_id"], "local_ops_default")
        self.assertEqual(invocation["provider_class"], "local_llm")
        self.assertEqual(invocation["capability_pack_ids"], ["readiness_probe_readonly", "core_status_readonly"])

        status = payload["status"]
        self.assertEqual(status["resolved_kind"], "task")
        self.assertEqual(status["status"], "DONE")
        self.assertEqual(status["result"]["actions_executed"], 1)
        report_path = Path(str(status["result"]["report_path"]))
        self.assertTrue(report_path.is_file())
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("stage8-readiness", report_text)
        self.assertIn("target_stage: 8", report_text)

        event_types = {item["event_type"] for item in payload["events"]["items"]}
        self.assertIn("TASK_ACTIONS_PLANNED", event_types)
        self.assertIn("PLANNED_ACTION_EXECUTED", event_types)
        self.assertTrue(payload["report"]["available"])
        self.assertEqual(payload["bundle"]["bundle_version"], "v1")
        self.assertEqual(payload["handoff"]["packet_type"], "completed")

    def test_job_contract_rejects_disallowed_profile_before_submission(self) -> None:
        payload, exit_code = cli_module._job_run_payload(
            template_id="daily_status_digest",
            profile_id="cloud_review_optional",
            input_payload=self._daily_status_input(),
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["error"]["code"], "INVALID_JOB_CONTRACT")
        self.assertIn("does not allow profile", payload["error"]["message"])


if __name__ == "__main__":
    unittest.main()
