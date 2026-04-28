from __future__ import annotations

import unittest
from pathlib import Path


try:
    from fastapi.testclient import TestClient
    from app import cli as cli_module
    from app import main as main_module
    from app.auth import issue_dev_jwt
    from tests.runtime_test_utils import reset_runtime_state
except Exception as exc:  # pragma: no cover - environment dependent
    TestClient = None
    cli_module = None
    main_module = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(cli_module is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestStage12JobInvocationSmoke(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)
        self.client = TestClient(main_module.APP)
        self.headers = {"Authorization": f"Bearer {issue_dev_jwt('qa_user', 'requester')}"}

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

    def _issue_triage_input(self) -> dict[str, object]:
        return {
            "issue_id": "ISSUE-123",
            "summary": "Internal documentation update request needs routing and a safe follow-up ticket draft.",
            "source_system": "helpdesk",
            "sensitivity": "internal",
            "service": "docs-portal",
            "labels": ["documentation", "low-risk"],
            "recent_events": [
                {
                    "timestamp": "2026-04-28T09:00:00Z",
                    "status": "new",
                    "summary": "Requester attached redacted reproduction notes.",
                }
            ],
            "redacted_context": "No customer data included.",
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
        self.assertTrue(by_id["issue_triage"]["executable"])
        self.assertIn("local_ops_default", by_id["readiness_check"]["compatible_profile_ids"])
        self.assertIn("issue_triage", list_payload["implemented_job_template_ids"])
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

    def test_job_history_surfaces_list_stage12_runs(self) -> None:
        run_payload, run_exit_code = cli_module._job_run_payload(
            template_id="daily_status_digest",
            profile_id="local_ops_default",
            input_payload=self._daily_status_input(),
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
            include_bundle=False,
            include_handoff=False,
            max_chars=1200,
            idempotency_key="qa-daily-status-2026-04-28",
        )
        self.assertEqual(run_exit_code, 0, run_payload)
        task_id = run_payload["status"]["task_id"]
        self.assertEqual(run_payload["job_invocation"]["idempotency_key"], "qa-daily-status-2026-04-28")
        self.assertTrue(run_payload["job_invocation"]["input_fingerprint"].startswith("sha256:"))

        history_payload, history_exit_code = cli_module._job_history_payload(
            limit=10,
            template_id="daily_status_digest",
            actor_id="qa_user",
            actor_role="requester",
        )
        self.assertEqual(history_exit_code, 0, history_payload)
        self.assertEqual(history_payload["surface"], "job.history")
        self.assertEqual(history_payload["template_filter"], "daily_status_digest")
        by_task = {item["task_id"]: item for item in history_payload["items"]}
        self.assertIn(task_id, by_task)
        item = by_task[task_id]
        self.assertEqual(item["template_id"], "daily_status_digest")
        self.assertEqual(item["profile_id"], "local_ops_default")
        self.assertTrue(item["budget_enforcement"]["enforced"])
        self.assertEqual(item["idempotency_key"], "qa-daily-status-2026-04-28")
        self.assertEqual(item["input_fingerprint"], run_payload["job_invocation"]["input_fingerprint"])
        self.assertEqual(item["state_summary"]["canonical_state"], "done")

    def test_issue_triage_job_runs_as_dry_run_incident(self) -> None:
        payload, exit_code = cli_module._job_run_payload(
            template_id="issue_triage",
            profile_id="local_ops_default",
            input_payload=self._issue_triage_input(),
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
            include_bundle=True,
            include_handoff=True,
            max_chars=2400,
        )

        self.assertEqual(exit_code, 0, payload)
        invocation = payload["job_invocation"]
        self.assertEqual(invocation["template_id"], "issue_triage")
        self.assertEqual(invocation["task_kind"], "incident")
        self.assertEqual(invocation["profile_id"], "local_ops_default")
        self.assertEqual(invocation["provider_class"], "local_llm")
        self.assertEqual(invocation["capability_pack_ids"], ["issue_triage_readonly", "ticket_draft_ops"])
        self.assertTrue(invocation["budget_enforcement"]["enforced"])
        self.assertFalse(invocation["budget_enforcement"]["budget_override_allowed"])

        status = payload["status"]
        self.assertEqual(status["resolved_kind"], "incident")
        self.assertEqual(status["status"], "DONE")
        self.assertEqual(status["run_mode"], "dry-run")
        self.assertEqual(status["result"]["actions_executed"], 1)
        report_path = Path(str(status["result"]["report_path"]))
        self.assertTrue(report_path.is_file())
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("ISSUE-123", report_text)
        self.assertIn("- run_mode: dry-run", report_text)

        event_types = {item["event_type"] for item in payload["events"]["items"]}
        self.assertIn("INCIDENT_ACTION_EXECUTED", event_types)
        self.assertIn("PLANNED_ACTION_EXECUTED", event_types)
        self.assertTrue(payload["report"]["available"])
        self.assertEqual(payload["bundle"]["bundle_version"], "v1")
        self.assertEqual(payload["handoff"]["packet_type"], "completed")

    def test_http_job_surfaces_discover_and_run_readiness_check(self) -> None:
        list_response = self.client.get("/api/v1/jobs", headers=self.headers)
        self.assertEqual(list_response.status_code, 200)
        by_id = {item["template_id"]: item for item in list_response.json()["items"]}
        self.assertTrue(by_id["readiness_check"]["executable"])

        describe_response = self.client.get(
            "/api/v1/jobs/readiness_check?profile_id=local_ops_default",
            headers=self.headers,
        )
        self.assertEqual(describe_response.status_code, 200)
        self.assertEqual(
            describe_response.json()["template"]["required_capability_packs"],
            ["readiness_probe_readonly", "core_status_readonly"],
        )

        run_response = self.client.post(
            "/api/v1/jobs/run",
            json={
                "template_id": "readiness_check",
                "profile_id": "local_ops_default",
                "requested_by": "qa_user",
                "idempotency_key": "qa-http-readiness-2026-04-28",
                "input": {
                    "check_set": "stage8-readiness",
                    "target_stage": 8,
                    "sensitivity": "internal",
                    "env_profile": "local",
                    "strict_gate": False,
                    "timeout_seconds": 15,
                },
                "include_bundle": True,
                "include_handoff": True,
                "max_chars": 2400,
            },
            headers=self.headers,
        )
        self.assertEqual(run_response.status_code, 202)
        payload = run_response.json()
        self.assertEqual(payload["job_invocation"]["template_id"], "readiness_check")
        self.assertEqual(payload["job_invocation"]["idempotency_key"], "qa-http-readiness-2026-04-28")
        self.assertEqual(payload["status"]["status"], "DONE")
        self.assertGreaterEqual(payload["events"]["count"], 4)
        self.assertTrue(payload["report"]["available"])
        self.assertEqual(payload["bundle"]["bundle_version"], "v1")
        self.assertEqual(payload["handoff"]["packet_type"], "completed")

        history_response = self.client.get(
            "/api/v1/jobs/runs?template_id=readiness_check&limit=10",
            headers=self.headers,
        )
        self.assertEqual(history_response.status_code, 200)
        history_payload = history_response.json()
        self.assertEqual(history_payload["surface"], "job.history")
        self.assertEqual(history_payload["template_filter"], "readiness_check")
        self.assertIn(
            payload["status"]["task_id"],
            {item["task_id"] for item in history_payload["items"]},
        )
        history_item = next(
            item for item in history_payload["items"] if item["task_id"] == payload["status"]["task_id"]
        )
        self.assertEqual(history_item["idempotency_key"], "qa-http-readiness-2026-04-28")

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

    def test_job_contract_rejects_budget_override_and_timeout_overrun(self) -> None:
        override_payload, override_exit_code = cli_module._job_run_payload(
            template_id="daily_status_digest",
            profile_id="local_ops_default",
            input_payload={
                **self._daily_status_input(),
                "execution_budget_override": {"max_tool_calls": 99},
            },
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
        )
        self.assertEqual(override_exit_code, 1)
        self.assertEqual(override_payload["error"]["code"], "INVALID_JOB_CONTRACT")
        self.assertIn("budget override requires an approval flow", override_payload["error"]["message"])

        timeout_payload, timeout_exit_code = cli_module._job_run_payload(
            template_id="readiness_check",
            profile_id="local_ops_default",
            input_payload={
                "check_set": "stage8-readiness",
                "target_stage": 8,
                "sensitivity": "internal",
                "timeout_seconds": 999,
            },
            requested_by="qa_user",
            actor_id="qa_user",
            actor_role="requester",
        )
        self.assertEqual(timeout_exit_code, 1)
        self.assertEqual(timeout_payload["error"]["code"], "INVALID_JOB_CONTRACT")
        self.assertIn("timeout_seconds exceeds max_elapsed_seconds", timeout_payload["error"]["message"])


if __name__ == "__main__":
    unittest.main()
