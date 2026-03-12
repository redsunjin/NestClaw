import unittest
from pathlib import Path


class TestStage8Contract(unittest.TestCase):
    def test_stage8_plan_doc_exists(self) -> None:
        self.assertTrue(Path("INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md").is_file())

    def test_stage8_checklist_doc_exists(self) -> None:
        self.assertTrue(Path("STAGE8_EXECUTION_CHECKLIST_2026-03-04.md").is_file())

    def test_stage8_detailed_design_doc_exists(self) -> None:
        self.assertTrue(Path("STAGE8_DETAILED_DESIGN_2026-03-04.md").is_file())

    def test_stage8_self_eval_group_doc_exists(self) -> None:
        self.assertTrue(Path("STAGE8_SELF_EVAL_GROUPS_2026-03-05.md").is_file())

    def test_stage8_closeout_summary_exists(self) -> None:
        self.assertTrue(Path("STAGE8_CLOSEOUT_SUMMARY_2026-03-06.md").is_file())

    def test_stage8_live_rehearsal_runbook_exists(self) -> None:
        self.assertTrue(Path("STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md").is_file())

    def test_micro_workflow_assets_exist(self) -> None:
        self.assertTrue(Path("MICRO_AGENT_WORKFLOW.md").is_file())
        self.assertTrue(Path("scripts/run_micro_cycle.sh").is_file())
        self.assertTrue(Path("scripts/run_stage8_self_eval.sh").is_file())
        self.assertTrue(Path("scripts/run_stage8_sandbox_e2e.sh").is_file())
        self.assertTrue(Path("scripts/run_stage8_live_rehearsal.sh").is_file())
        self.assertTrue(Path("scripts/stage8_live_rehearsal_runner.py").is_file())
        self.assertTrue(Path("work/micro_units/stage8-w2-001/WORK_UNIT.md").is_file())
        self.assertTrue(Path("work/micro_units/stage8-w3-002/WORK_UNIT.md").is_file())
        self.assertTrue(Path("work/micro_units/stage8-w4-001/WORK_UNIT.md").is_file())
        self.assertTrue(Path("app/incident_rag.py").is_file())
        self.assertTrue(Path("app/incident_mcp.py").is_file())
        self.assertTrue(Path("app/incident_policy.py").is_file())
        self.assertTrue(Path("app/model_registry.py").is_file())
        self.assertTrue(Path("app/intent_classifier.py").is_file())
        self.assertTrue(Path("app/services/approval_service.py").is_file())
        self.assertTrue(Path("app/services/orchestration_service.py").is_file())
        self.assertTrue(Path("app/mcp_server.py").is_file())
        self.assertTrue(Path("tests/test_model_registry_contract.py").is_file())
        self.assertTrue(Path("tests/test_model_registry_runtime.py").is_file())
        self.assertTrue(Path("tests/test_intent_classifier_contract.py").is_file())
        self.assertTrue(Path("tests/test_intent_classifier_runtime.py").is_file())
        self.assertTrue(Path("tests/test_incident_adapter_contract.py").is_file())
        self.assertTrue(Path("tests/test_agent_entrypoint_smoke.py").is_file())
        self.assertTrue(Path("tests/test_incident_runtime_smoke.py").is_file())
        self.assertTrue(Path("tests/test_tool_cli_smoke.py").is_file())
        self.assertTrue(Path("tests/test_mcp_server_smoke.py").is_file())
        self.assertTrue(Path("tests/test_incident_policy_gate.py").is_file())

    def test_detailed_design_includes_required_contract_sections(self) -> None:
        source = Path("STAGE8_DETAILED_DESIGN_2026-03-04.md").read_text(encoding="utf-8")
        self.assertIn("Incident Intake 객체", source)
        self.assertIn("RAG 계약", source)
        self.assertIn("Action Card 스키마", source)
        self.assertIn("승인 분류표", source)
        self.assertIn("QA 설계", source)

    def test_checklist_includes_kpi_and_weekly_phases(self) -> None:
        source = Path("STAGE8_EXECUTION_CHECKLIST_2026-03-04.md").read_text(encoding="utf-8")
        self.assertIn("KPI (Go/No-Go 기준)", source)
        self.assertIn("Week 1", source)
        self.assertIn("Week 4", source)
        self.assertIn("Week 6-7", source)

    def test_tasks_include_stage8_schedule(self) -> None:
        source = Path("TASKS.md").read_text(encoding="utf-8")
        self.assertIn("Stage 8 실행 스케줄", source)
        self.assertIn("2026-03-05 ~ 2026-03-06", source)

    def test_next_stage_plan_includes_stage8_schedule_update(self) -> None:
        source = Path("NEXT_STAGE_PLAN_2026-02-24.md").read_text(encoding="utf-8")
        self.assertIn("Stage 8 실행 스케줄 업데이트", source)
        self.assertIn("2026-04-13 ~ 2026-04-24", source)

    def test_dev_qa_cycle_supports_stage8(self) -> None:
        source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..8", source)
        self.assertIn("check_stage_8", source)
        self.assertIn("tests.test_stage8_contract", source)
        self.assertIn("tests.test_model_registry_contract", source)
        self.assertIn("tests.test_intent_classifier_contract", source)
        self.assertIn("tests.test_incident_adapter_contract", source)
        self.assertIn("tests.test_incident_policy_gate", source)
        self.assertIn("tests.test_model_registry_runtime", source)
        self.assertIn("tests.test_intent_classifier_runtime", source)
        self.assertIn("tests.test_agent_entrypoint_smoke", source)
        self.assertIn("tests.test_incident_runtime_smoke", source)
        self.assertIn("tests.test_tool_cli_smoke", source)
        self.assertIn("tests.test_mcp_server_smoke", source)
        self.assertIn("run_stage8_self_eval.sh", source)
        self.assertIn("run_stage8_sandbox_e2e.sh", source)
        self.assertIn("run_stage8_live_rehearsal.sh", source)
        self.assertIn("NEWCLAW_SKIP_STAGE8_SELF_EVAL", source)

    def test_auto_cycle_supports_stage8(self) -> None:
        source = Path("scripts/run_auto_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage:1..8", source)
        self.assertIn("target-stage must be 1..8", source)

    def test_micro_cycle_supports_stage8_gate_flow(self) -> None:
        source = Path("scripts/run_micro_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("gate-plan", source)
        self.assertIn("gate-review", source)
        self.assertIn("gate-implement", source)
        self.assertIn("gate-evaluate", source)
        self.assertIn("run_dev_qa_cycle.sh", source)
        self.assertIn("NEWCLAW_SKIP_STAGE8_SELF_EVAL=1", source)
        self.assertIn("mkdir -p \"$(unit_dir \"$unit_id\")/reports\"", source)

    def test_self_eval_handles_runtime_skip_for_g2(self) -> None:
        source = Path("scripts/run_stage8_self_eval.sh").read_text(encoding="utf-8")
        self.assertIn("run_check_allow_skip", source)
        self.assertIn("skipped=[1-9]", source)
        self.assertIn("G2 (runtime smoke skipped)", source)

    def test_self_eval_requires_passed_sandbox_report_for_g4(self) -> None:
        source = Path("scripts/run_stage8_self_eval.sh").read_text(encoding="utf-8")
        self.assertIn('tail -n 20 "${latest_sandbox_report}"', source)
        self.assertIn('rg -q -- "^- status: PASS$"', source)
        self.assertIn("run_stage8_sandbox_e2e.sh", source)
        self.assertIn("NEWCLAW_SKIP_STAGE8_SELF_EVAL=1", source)

    def test_self_eval_group_doc_has_four_groups(self) -> None:
        source = Path("STAGE8_SELF_EVAL_GROUPS_2026-03-05.md").read_text(encoding="utf-8")
        self.assertIn("G1. Adapter Contract Foundation", source)
        self.assertIn("G2. Incident Orchestration Integration", source)
        self.assertIn("G3. Policy & Approval Classification", source)
        self.assertIn("G4. Quality Gate & Sandbox Readiness", source)

    def test_incident_runtime_supports_mcp_live_mode(self) -> None:
        source = Path("app/main.py").read_text(encoding="utf-8")
        self.assertIn("mcp-live", source)
        self.assertIn("context_dry_run", source)
        self.assertIn("mcp_dry_run", source)

    def test_main_uses_orchestration_service_layer(self) -> None:
        source = Path("app/main.py").read_text(encoding="utf-8")
        self.assertIn("ORCHESTRATION_SERVICE", source)
        self.assertIn("APPROVAL_SERVICE", source)
        self.assertIn("OrchestrationServiceDeps", source)
        self.assertIn("task_status_ready=TaskStatus.READY,", source)
        self.assertIn("task_status_running=TaskStatus.RUNNING,", source)

    def test_orchestration_service_normalizes_status_enum_to_string(self) -> None:
        source = Path("app/services/orchestration_service.py").read_text(encoding="utf-8")
        self.assertIn("def _status_value", source)
        self.assertIn('self.deps.set_status(task, self.deps.task_status_running', source)
        self.assertIn('"status": self._status_value(self.deps.task_status_ready)', source)

    def test_cli_supports_non_interactive_tool_commands(self) -> None:
        source = Path("app/cli.py").read_text(encoding="utf-8")
        self.assertIn('subparsers.add_parser("submit"', source)
        self.assertIn('subparsers.add_parser("status"', source)
        self.assertIn('subparsers.add_parser("events"', source)
        self.assertIn('subparsers.add_parser("approve"', source)
        self.assertIn('subparsers.add_parser("reject"', source)
        self.assertIn("build_orchestration_service(sync_execution=True)", source)
        self.assertIn("build_approval_service(sync_execution=True)", source)

    def test_mcp_server_exposes_required_tools(self) -> None:
        source = Path("app/mcp_server.py").read_text(encoding="utf-8")
        self.assertIn("SUPPORTED_PROTOCOL_VERSIONS", source)
        self.assertIn('"agent.submit"', source)
        self.assertIn('"agent.status"', source)
        self.assertIn('"agent.events"', source)
        self.assertIn('"approval.list"', source)
        self.assertIn('"approval.approve"', source)
        self.assertIn('"approval.reject"', source)
        self.assertIn('method == "tools/list"', source)
        self.assertIn('method == "tools/call"', source)

    def test_model_registry_is_connected_to_runtime_selection(self) -> None:
        source = Path("app/main.py").read_text(encoding="utf-8")
        self.assertIn("MODEL_REGISTRY = load_model_registry()", source)
        self.assertIn("MODEL_PROVIDER_SELECTED", source)
        self.assertIn("provider_selection", source)

    def test_intent_classifier_is_connected_to_agent_runtime(self) -> None:
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        service_source = Path("app/services/orchestration_service.py").read_text(encoding="utf-8")
        classifier_source = Path("app/intent_classifier.py").read_text(encoding="utf-8")
        registry_source = Path("configs/model_registry.yaml").read_text(encoding="utf-8")
        self.assertIn("INTENT_CLASSIFIER = IntentClassifier(MODEL_REGISTRY)", main_source)
        self.assertIn("classify_agent_intent=_classify_agent_intent", main_source)
        self.assertIn("INTENT_CLASSIFIED", service_source)
        self.assertIn("intent_classification", service_source)
        self.assertIn("NEWCLAW_ENABLE_LLM_INTENT", classifier_source)
        self.assertIn("task_type: classify_intent", registry_source)

    def test_live_rehearsal_runbook_mentions_http_bridge_contract(self) -> None:
        source = Path("STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md").read_text(encoding="utf-8")
        self.assertIn("NEWCLAW_REDMINE_MCP_ENDPOINT", source)
        self.assertIn("mcp-live", source)
        self.assertIn("issue.transition", source)


if __name__ == "__main__":
    unittest.main()
