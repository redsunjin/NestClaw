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
        self.assertTrue(Path("app/provider_invoker.py").is_file())
        self.assertTrue(Path("app/tool_registry.py").is_file())
        self.assertTrue(Path("app/intent_classifier.py").is_file())
        self.assertTrue(Path("app/static/agent-console.html").is_file())
        self.assertTrue(Path("app/static/agent-console.css").is_file())
        self.assertTrue(Path("app/static/agent-console.js").is_file())
        self.assertTrue(Path("app/services/approval_service.py").is_file())
        self.assertTrue(Path("app/services/orchestration_service.py").is_file())
        self.assertTrue(Path("app/services/tool_catalog_service.py").is_file())
        self.assertTrue(Path("app/mcp_server.py").is_file())
        self.assertTrue(Path("tests/test_model_registry_contract.py").is_file())
        self.assertTrue(Path("tests/test_model_registry_runtime.py").is_file())
        self.assertTrue(Path("tests/test_provider_invoker_contract.py").is_file())
        self.assertTrue(Path("tests/test_provider_invoker_runtime.py").is_file())
        self.assertTrue(Path("tests/test_tool_registry_contract.py").is_file())
        self.assertTrue(Path("tests/test_tool_registry_runtime.py").is_file())
        self.assertTrue(Path("tests/test_intent_classifier_contract.py").is_file())
        self.assertTrue(Path("tests/test_intent_classifier_runtime.py").is_file())
        self.assertTrue(Path("tests/test_incident_adapter_contract.py").is_file())
        self.assertTrue(Path("tests/test_agent_entrypoint_smoke.py").is_file())
        self.assertTrue(Path("tests/test_incident_runtime_smoke.py").is_file())
        self.assertTrue(Path("tests/test_tool_cli_smoke.py").is_file())
        self.assertTrue(Path("tests/test_mcp_server_smoke.py").is_file())
        self.assertTrue(Path("tests/test_incident_policy_gate.py").is_file())
        self.assertTrue(Path("tests/test_web_console_runtime.py").is_file())

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

    def test_product_definition_aligns_with_tool_using_execution_agent(self) -> None:
        readme_source = Path("README.md").read_text(encoding="utf-8")
        onepager_source = Path("IDEATION_ONEPAGER.md").read_text(encoding="utf-8")
        direction_source = Path("AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md").read_text(encoding="utf-8")
        self.assertIn("다양한 도구를 사용하는 업무 실행", readme_source)
        self.assertIn("다양한 도구를 사용하는 업무 실행 에이전트", onepager_source)
        self.assertIn("다양한 도구를 정책적으로 사용하는 실행형 에이전트", direction_source)

    def test_stage8_docs_position_incident_as_first_vertical(self) -> None:
        plan_source = Path("INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md").read_text(encoding="utf-8")
        closeout_source = Path("STAGE8_CLOSEOUT_SUMMARY_2026-03-06.md").read_text(encoding="utf-8")
        tasks_source = Path("TASKS.md").read_text(encoding="utf-8")
        self.assertIn("첫 번째 vertical", plan_source)
        self.assertIn("broader execution agent", plan_source)
        self.assertIn("첫 번째 high-risk vertical", closeout_source)
        self.assertIn("첫 번째 vertical: 운영장애 대응 오케스트레이션", tasks_source)

    def test_api_contract_documents_current_workflow_family_scope(self) -> None:
        source = Path("API_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("현재 v0.1 구현 범위의 workflow family는 `task`와 `incident`", source)
        self.assertIn("LLM intent classifier + heuristic fallback", source)
        self.assertIn("broader tool registry / planner / execution adapter", source)

    def test_dev_qa_cycle_supports_stage8(self) -> None:
        source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("target-stage: 1..8", source)
        self.assertIn("check_stage_8", source)
        self.assertIn("tests.test_stage8_contract", source)
        self.assertIn("tests.test_model_registry_contract", source)
        self.assertIn("tests.test_provider_invoker_contract", source)
        self.assertIn("tests.test_tool_registry_contract", source)
        self.assertIn("tests.test_intent_classifier_contract", source)
        self.assertIn("tests.test_incident_adapter_contract", source)
        self.assertIn("tests.test_incident_policy_gate", source)
        self.assertIn("tests.test_model_registry_runtime", source)
        self.assertIn("tests.test_provider_invoker_runtime", source)
        self.assertIn("tests.test_tool_registry_runtime", source)
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
        self.assertIn("TOOL_CATALOG_SERVICE", source)
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
        self.assertIn('subparsers.add_parser("tools"', source)
        self.assertIn('subparsers.add_parser("tool-draft"', source)
        self.assertIn('subparsers.add_parser("tool-apply"', source)
        self.assertIn("build_orchestration_service(sync_execution=True)", source)
        self.assertIn("build_approval_service(sync_execution=True)", source)
        self.assertIn("build_tool_catalog_service()", source)
        self.assertIn("build_tool_draft_service()", source)

    def test_mcp_server_exposes_required_tools(self) -> None:
        source = Path("app/mcp_server.py").read_text(encoding="utf-8")
        self.assertIn("SUPPORTED_PROTOCOL_VERSIONS", source)
        self.assertIn('"agent.submit"', source)
        self.assertIn('"agent.status"', source)
        self.assertIn('"agent.events"', source)
        self.assertIn('"approval.list"', source)
        self.assertIn('"approval.approve"', source)
        self.assertIn('"approval.reject"', source)
        self.assertIn('"catalog.list"', source)
        self.assertIn('"catalog.get"', source)
        self.assertIn('"catalog.create_draft"', source)
        self.assertIn('"catalog.get_draft"', source)
        self.assertIn('"catalog.apply_draft"', source)
        self.assertIn('method == "tools/list"', source)
        self.assertIn('method == "tools/call"', source)

    def test_model_registry_is_connected_to_runtime_selection(self) -> None:
        source = Path("app/main.py").read_text(encoding="utf-8")
        self.assertIn("MODEL_REGISTRY = load_model_registry()", source)
        self.assertIn("MODEL_PROVIDER_SELECTED", source)
        self.assertIn("provider_selection", source)

    def test_provider_invoker_is_connected_to_summary_runtime(self) -> None:
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        service_source = Path("app/services/orchestration_service.py").read_text(encoding="utf-8")
        invoker_source = Path("app/provider_invoker.py").read_text(encoding="utf-8")
        self.assertIn("PROVIDER_INVOKER = ProviderInvoker()", main_source)
        self.assertIn("MODEL_PROVIDER_INVOKED", main_source)
        self.assertIn("invoke_meeting_summary", main_source)
        self.assertIn("internal.summary.generate", main_source)
        self.assertIn("planned_actions", main_source)
        self.assertIn("execution_call", main_source)
        self.assertIn("PLANNED_ACTION_EXECUTED", main_source)
        self.assertIn("provider_invocation", service_source)
        self.assertIn("planned_actions", service_source)
        self.assertIn("action_results", service_source)
        self.assertIn("NEWCLAW_ENABLE_LLM_SUMMARY", invoker_source)
        self.assertIn("result_source", invoker_source)

    def test_tool_registry_is_connected_to_runtime_execution_surfaces(self) -> None:
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        cli_source = Path("app/cli.py").read_text(encoding="utf-8")
        mcp_source = Path("app/mcp_server.py").read_text(encoding="utf-8")
        registry_source = Path("configs/tool_registry.yaml").read_text(encoding="utf-8")
        self.assertIn("TOOL_REGISTRY = load_tool_registry()", main_source)
        self.assertIn('"/api/v1/tools"', main_source)
        self.assertIn('"/api/v1/tool-drafts"', main_source)
        self.assertIn('"/api/v1/tool-drafts/{draft_id}/apply"', main_source)
        self.assertIn('"tool_id": capability.tool_id', main_source)
        self.assertIn("CLI_TOOL_CATALOG_SERVICE", cli_source)
        self.assertIn("CLI_TOOL_DRAFT_SERVICE", cli_source)
        self.assertIn("catalog.list", mcp_source)
        self.assertIn("catalog.create_draft", mcp_source)
        self.assertIn("catalog.apply_draft", mcp_source)
        self.assertIn("internal.summary.generate", registry_source)
        self.assertIn("redmine.issue.create", registry_source)
        self.assertIn("slack.message.send", registry_source)
        self.assertIn("required_payload_fields", registry_source)

    def test_web_console_is_exposed_from_root(self) -> None:
        main_source = Path("app/main.py").read_text(encoding="utf-8")
        readme_source = Path("README.md").read_text(encoding="utf-8")
        self.assertIn('APP.mount("/static"', main_source)
        self.assertIn('@APP.get("/", include_in_schema=False)', main_source)
        self.assertIn("최소 Web Console", readme_source)
        self.assertIn("http://127.0.0.1:8000/", readme_source)

    def test_slack_adapter_and_tool_draft_service_exist(self) -> None:
        slack_source = Path("app/slack_adapter.py").read_text(encoding="utf-8")
        service_source = Path("app/services/tool_draft_service.py").read_text(encoding="utf-8")
        self.assertIn("def execute_slack_action", slack_source)
        self.assertIn("NEWCLAW_ENABLE_SLACK_LIVE", slack_source)
        self.assertIn("class ToolDraftService", service_source)
        self.assertIn("DRAFT_REVIEW_REQUIRED", service_source)
        self.assertIn("apply_draft", service_source)

    def test_tool_registry_overlay_support_is_connected(self) -> None:
        source = Path("app/tool_registry.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_TOOL_REGISTRY_OVERLAY_PATH", source)
        self.assertIn("upsert_tool_registry_tool", source)
        self.assertIn("render_tool_registry", source)

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
        self.assertIn("NEWCLAW_LMSTUDIO_BASE_URL", classifier_source)
        self.assertIn("_call_openai_compatible_chat", classifier_source)
        self.assertIn("engine: lmstudio", registry_source)
        self.assertIn("task_type: classify_intent", registry_source)

    def test_live_rehearsal_runbook_mentions_http_bridge_contract(self) -> None:
        source = Path("STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md").read_text(encoding="utf-8")
        self.assertIn("NEWCLAW_REDMINE_MCP_ENDPOINT", source)
        self.assertIn("mcp-live", source)
        self.assertIn("issue.transition", source)


if __name__ == "__main__":
    unittest.main()
